from pydub import AudioSegment
from io import BytesIO
from Libs.Logger import Logger
from Libs.Shazam.Utils.Communication_S import recognize_song_from_signature
from Libs.Shazam.Utils.Algorithm_S import SignatureGenerator
from youtubesearchpython import VideosSearch


class ShazamUtil:
    def __init__(self, log: Logger):
        self.log = log

    def song_name(self, song_bytes):
        audio: AudioSegment = AudioSegment.from_file(BytesIO(song_bytes))
        audio = audio.set_sample_width(2)
        audio = audio.set_frame_rate(16000)
        audio = audio.set_channels(1)
        signature_generator = SignatureGenerator()
        signature_generator.feed_input(audio.get_array_of_samples())
        signature_generator.MAX_TIME_SECONDS = 12
        if audio.duration_seconds > 12 * 3:
            signature_generator.samples_processed += 16000 * (
                int(audio.duration_seconds / 2) - 6
            )
        results = "(Not enough data)"
        while True:
            signature = signature_generator.get_next_signature()
            if not signature:
                return {"short_result": None, "full_result": None}
            results = recognize_song_from_signature(signature)
            if results["matches"]:
                title = results["track"]["title"]
                artist = results["track"]["subtitle"]
                images = results["track"]["images"]
                full_title = results["track"]["share"]["subject"]
                shazam_url = results["track"]["share"]["href"]
                yt_results = VideosSearch(full_title, limit=15)
                return {
                    "short_result": {
                        "name": title,
                        "artist": artist,
                        "images": images,
                        "full_title": full_title,
                        "youtube_results": yt_results.result(),
                        "shazam_url": shazam_url,
                    },
                    "full_result": results,
                }
            else:
                self.log.error(
                    "No matching songs for the first %g seconds, typing to recognize more input..."
                    % (signature_generator.samples_processed / 16000)
                )
