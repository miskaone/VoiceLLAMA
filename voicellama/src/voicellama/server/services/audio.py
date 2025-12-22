"""
Audio Processing Utilities

Provides audio format conversion, compression, and streaming utilities
for optimized TTS delivery.
"""
import io
import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple, Union
import numpy as np


class AudioEncoder:
    """
    Audio encoder supporting multiple output formats.

    Supports:
    - WAV (uncompressed, best quality)
    - MP3 (compressed, good browser support)
    - OGG/Opus (compressed, best quality/size ratio)
    """

    FORMATS = {
        'wav': {
            'mime_type': 'audio/wav',
            'extension': '.wav',
            'requires_ffmpeg': False
        },
        'mp3': {
            'mime_type': 'audio/mpeg',
            'extension': '.mp3',
            'requires_ffmpeg': True,
            'ffmpeg_codec': 'libmp3lame',
            'default_bitrate': '128k'
        },
        'ogg': {
            'mime_type': 'audio/ogg',
            'extension': '.ogg',
            'requires_ffmpeg': True,
            'ffmpeg_codec': 'libopus',
            'default_bitrate': '96k'
        }
    }

    def __init__(self):
        """Initialize encoder and check for ffmpeg."""
        self._ffmpeg_available = self._check_ffmpeg()

    def _check_ffmpeg(self) -> bool:
        """Check if ffmpeg is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    @property
    def ffmpeg_available(self) -> bool:
        """Check if ffmpeg is available for compression."""
        return self._ffmpeg_available

    def get_supported_formats(self) -> list:
        """Get list of supported output formats."""
        formats = ['wav']
        if self._ffmpeg_available:
            formats.extend(['mp3', 'ogg'])
        return formats

    def encode(
        self,
        audio_data: Union[np.ndarray, bytes],
        sample_rate: int,
        output_format: str = 'wav',
        bitrate: Optional[str] = None,
        input_is_wav_bytes: bool = False
    ) -> Tuple[bytes, str]:
        """
        Encode audio to the specified format.

        Args:
            audio_data: Audio as numpy array or WAV bytes
            sample_rate: Sample rate in Hz
            output_format: Output format ('wav', 'mp3', 'ogg')
            bitrate: Bitrate for compressed formats (e.g., '128k')
            input_is_wav_bytes: True if audio_data is already WAV bytes

        Returns:
            Tuple of (encoded_bytes, mime_type)
        """
        output_format = output_format.lower()
        if output_format not in self.FORMATS:
            raise ValueError(f"Unsupported format: {output_format}. Supported: {list(self.FORMATS.keys())}")

        format_config = self.FORMATS[output_format]

        if output_format == 'wav':
            if input_is_wav_bytes:
                return audio_data, format_config['mime_type']
            else:
                wav_bytes = self._numpy_to_wav(audio_data, sample_rate)
                return wav_bytes, format_config['mime_type']

        if not self._ffmpeg_available:
            raise RuntimeError(f"ffmpeg required for {output_format} encoding but not available")

        if input_is_wav_bytes:
            wav_bytes = audio_data
        else:
            wav_bytes = self._numpy_to_wav(audio_data, sample_rate)

        bitrate = bitrate or format_config['default_bitrate']
        encoded_bytes = self._ffmpeg_encode(
            wav_bytes,
            format_config['ffmpeg_codec'],
            bitrate,
            format_config['extension']
        )

        return encoded_bytes, format_config['mime_type']

    def _numpy_to_wav(self, audio: np.ndarray, sample_rate: int) -> bytes:
        """Convert numpy array to WAV bytes."""
        import soundfile as sf

        buffer = io.BytesIO()
        sf.write(buffer, audio, sample_rate, format='WAV', subtype='PCM_16')
        buffer.seek(0)
        return buffer.read()

    def _ffmpeg_encode(
        self,
        wav_bytes: bytes,
        codec: str,
        bitrate: str,
        extension: str
    ) -> bytes:
        """Use ffmpeg to encode audio."""
        with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
            wav_file.write(wav_bytes)
            wav_path = wav_file.name

        output_path = wav_path.replace('.wav', extension)

        try:
            cmd = [
                'ffmpeg', '-y',
                '-i', wav_path,
                '-c:a', codec,
                '-b:a', bitrate,
                '-vn',
                output_path
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                timeout=30
            )

            if result.returncode != 0:
                raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")

            with open(output_path, 'rb') as f:
                encoded_bytes = f.read()

            return encoded_bytes

        finally:
            Path(wav_path).unlink(missing_ok=True)
            Path(output_path).unlink(missing_ok=True)

    def get_format_info(self, format_name: str) -> dict:
        """Get information about a format."""
        if format_name not in self.FORMATS:
            return None
        info = self.FORMATS[format_name].copy()
        info['available'] = not info.get('requires_ffmpeg', False) or self._ffmpeg_available
        return info


class StreamingAudioBuffer:
    """Buffer for streaming audio generation."""

    def __init__(self, sample_rate: int = 24000):
        """Initialize the streaming buffer."""
        self.sample_rate = sample_rate
        self.chunks: list = []
        self.total_samples = 0

    def add_chunk(self, audio: np.ndarray) -> None:
        """Add an audio chunk to the buffer."""
        self.chunks.append(audio)
        self.total_samples += len(audio)

    def get_duration_seconds(self) -> float:
        """Get total duration of buffered audio."""
        return self.total_samples / self.sample_rate

    def get_all(self) -> np.ndarray:
        """Get all audio as a single numpy array."""
        if not self.chunks:
            return np.array([], dtype=np.float32)
        return np.concatenate(self.chunks)

    def clear(self) -> None:
        """Clear the buffer."""
        self.chunks.clear()
        self.total_samples = 0


# Global encoder instance
audio_encoder = AudioEncoder()
