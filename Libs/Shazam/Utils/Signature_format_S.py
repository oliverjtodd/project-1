from typing import Dict, List
from base64 import b64decode, b64encode
from math import exp, sqrt
from binascii import crc32
from enum import IntEnum
from io import BytesIO
from ctypes import *

DATA_URI_PREFIX = "data:audio/vnd.shazam.sig;base64,"


class SampleRate(IntEnum):

    _8000 = 1
    _11025 = 2
    _16000 = 3
    _32000 = 4
    _44100 = 5
    _48000 = 6


class FrequencyBand(IntEnum):

    _0_250 = -1
    _250_520 = 0
    _520_1450 = 1
    _1450_3500 = 2
    _3500_5500 = 3


class RawSignatureHeader(LittleEndianStructure):

    _pack = True

    _fields_ = [
        ("magic1", c_uint32),
        ("crc32", c_uint32),
        ("size_minus_header", c_uint32),
        ("magic2", c_uint32),
        ("void1", c_uint32 * 3),
        ("shifted_sample_rate_id", c_uint32),
        ("void2", c_uint32 * 2),
        ("number_samples_plus_divided_sample_rate", c_uint32),
        ("fixed_value", c_uint32),
    ]


class FrequencyPeak:

    fft_pass_number: int = None
    peak_magnitude: int = None
    corrected_peak_frequency_bin: int = None
    sample_rate_hz: int = None

    def __init__(
        self,
        fft_pass_number: int,
        peak_magnitude: int,
        corrected_peak_frequency_bin: int,
        sample_rate_hz: int,
    ):

        self.fft_pass_number = fft_pass_number
        self.peak_magnitude = peak_magnitude
        self.corrected_peak_frequency_bin = corrected_peak_frequency_bin
        self.sample_rate_hz = sample_rate_hz

    def get_frequency_hz(self) -> float:

        return self.corrected_peak_frequency_bin * (self.sample_rate_hz / 2 / 1024 / 64)

    def get_amplitude_pcm(self) -> float:

        return sqrt(exp((self.peak_magnitude - 6144) / 1477.3) * (1 << 17) / 2) / 1024

    def get_seconds(self) -> float:

        return (self.fft_pass_number * 128) / self.sample_rate_hz


class DecodedMessage:

    sample_rate_hz: int = None
    number_samples: int = None

    frequency_band_to_sound_peaks: Dict[FrequencyBand, List[FrequencyPeak]] = None

    @classmethod
    def decode_from_binary(cls, data: bytes):

        self = cls()

        buf = BytesIO(data)

        buf.seek(8)
        checksummable_data = buf.read()
        buf.seek(0)

        header = RawSignatureHeader()
        buf.readinto(header)

        assert header.magic1 == 0xCAFE2580
        assert header.size_minus_header == len(data) - 48
        assert crc32(checksummable_data) & 0xFFFFFFFF == header.crc32
        assert header.magic2 == 0x94119C00

        self.sample_rate_hz = int(
            SampleRate(header.shifted_sample_rate_id >> 27).name.strip("_")
        )

        self.number_samples = int(
            header.number_samples_plus_divided_sample_rate - self.sample_rate_hz * 0.24
        )

        assert int.from_bytes(buf.read(4), "little") == 0x40000000
        assert int.from_bytes(buf.read(4), "little") == len(data) - 48

        self.frequency_band_to_sound_peaks = {}

        while True:

            tlv_header = buf.read(8)
            if not tlv_header:
                break

            frequency_band_id = int.from_bytes(tlv_header[:4], "little")
            frequency_peaks_size = int.from_bytes(tlv_header[4:], "little")

            frequency_peaks_padding = -frequency_peaks_size % 4

            frequency_peaks_buf = BytesIO(buf.read(frequency_peaks_size))
            buf.read(frequency_peaks_padding)

            frequency_band = FrequencyBand(frequency_band_id - 0x60030040)

            fft_pass_number = 0

            self.frequency_band_to_sound_peaks[frequency_band] = []

            while True:

                raw_fft_pass: bytes = frequency_peaks_buf.read(1)
                if not raw_fft_pass:
                    break

                fft_pass_offset: int = raw_fft_pass[0]
                if fft_pass_offset == 0xFF:
                    fft_pass_number = int.from_bytes(
                        frequency_peaks_buf.read(4), "little"
                    )
                    continue
                else:
                    fft_pass_number += fft_pass_offset

                peak_magnitude = int.from_bytes(frequency_peaks_buf.read(2), "little")
                corrected_peak_frequency_bin = int.from_bytes(
                    frequency_peaks_buf.read(2), "little"
                )

                self.frequency_band_to_sound_peaks[frequency_band].append(
                    FrequencyPeak(
                        fft_pass_number,
                        peak_magnitude,
                        corrected_peak_frequency_bin,
                        self.sample_rate_hz,
                    )
                )

        return self

    @classmethod
    def decode_from_uri(cls, uri: str):

        assert uri.startswith(DATA_URI_PREFIX)

        return cls.decode_from_binary(b64decode(uri.replace(DATA_URI_PREFIX, "", 1)))

    """
        Encode the current object to a readable JSON format, for debugging
        purposes.
    """

    def encode_to_json(self) -> dict:

        return {
            "sample_rate_hz": self.sample_rate_hz,
            "number_samples": self.number_samples,
            "_seconds": self.number_samples / self.sample_rate_hz,
            "frequency_band_to_peaks": {
                frequency_band.name.strip("_"): [
                    {
                        "fft_pass_number": frequency_peak.fft_pass_number,
                        "peak_magnitude": frequency_peak.peak_magnitude,
                        "corrected_peak_frequency_bin": frequency_peak.corrected_peak_frequency_bin,
                        "_frequency_hz": frequency_peak.get_frequency_hz(),
                        "_amplitude_pcm": frequency_peak.get_amplitude_pcm(),
                        "_seconds": frequency_peak.get_seconds(),
                    }
                    for frequency_peak in frequency_peaks
                ]
                for frequency_band, frequency_peaks in sorted(
                    self.frequency_band_to_sound_peaks.items()
                )
            },
        }

    def encode_to_binary(self) -> bytes:

        header = RawSignatureHeader()

        header.magic1 = 0xCAFE2580
        header.magic2 = 0x94119C00
        header.shifted_sample_rate_id = (
            int(getattr(SampleRate, "_%s" % self.sample_rate_hz)) << 27
        )
        header.fixed_value = (15 << 19) + 0x40000
        header.number_samples_plus_divided_sample_rate = int(
            self.number_samples + self.sample_rate_hz * 0.24
        )

        contents_buf = BytesIO()

        for frequency_band, frequency_peaks in sorted(
            self.frequency_band_to_sound_peaks.items()
        ):

            peaks_buf = BytesIO()

            fft_pass_number = 0

            for frequency_peak in frequency_peaks:

                assert frequency_peak.fft_pass_number >= fft_pass_number

                if frequency_peak.fft_pass_number - fft_pass_number >= 255:

                    peaks_buf.write(b"\xff")
                    peaks_buf.write(
                        (frequency_peak.fft_pass_number).to_bytes(4, "little")
                    )

                    fft_pass_number = frequency_peak.fft_pass_number

                peaks_buf.write(
                    bytes([frequency_peak.fft_pass_number - fft_pass_number])
                )
                peaks_buf.write((frequency_peak.peak_magnitude).to_bytes(2, "little"))
                peaks_buf.write(
                    (frequency_peak.corrected_peak_frequency_bin).to_bytes(2, "little")
                )

                fft_pass_number = frequency_peak.fft_pass_number

            contents_buf.write((0x60030040 + int(frequency_band)).to_bytes(4, "little"))
            contents_buf.write(len(peaks_buf.getvalue()).to_bytes(4, "little"))
            contents_buf.write(peaks_buf.getvalue())
            contents_buf.write(b"\x00" * (-len(peaks_buf.getvalue()) % 4))

        header.size_minus_header = len(contents_buf.getvalue()) + 8

        buf = BytesIO()
        buf.write(bytes(header))

        buf.write((0x40000000).to_bytes(4, "little"))
        buf.write((len(contents_buf.getvalue()) + 8).to_bytes(4, "little"))

        buf.write(contents_buf.getvalue())

        buf.seek(8)
        header.crc32 = crc32(buf.read()) & 0xFFFFFFFF
        buf.seek(0)
        buf.write(bytes(header))

        return buf.getvalue()

    def encode_to_uri(self) -> str:

        return DATA_URI_PREFIX + b64encode(self.encode_to_binary()).decode("ascii")
