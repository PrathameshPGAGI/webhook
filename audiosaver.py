import requests
import base64
import wave
import numpy as np
import json

def get_and_save_audio(base_url, bot_id, output_filename="output_audio.wav"):
    """
    Get audio data from the API, convert to playable format and save as WAV
    """
    try:
        # Send GET request to the audio endpoint
        response = requests.get(f"{base_url}/audio/{bot_id}")
        response.raise_for_status()
        
        # Parse JSON response
        audio_data = response.json()
        
        if "error" in audio_data:
            print(f"Error from API: {audio_data['error']}")
            return False
            
        combined_buffer = audio_data.get("combined_buffer")
        if not combined_buffer:
            print("No audio buffer found in response")
            return False
            
        print(f"Received audio data for bot_id: {audio_data['bot_id']}")
        print(f"First timestamp: {audio_data['first_timestamp']}")
        print(f"Last timestamp: {audio_data['last_timestamp']}")
        print(f"Total audio records: {audio_data['total_records']}")
        print(f"Combined buffer length (base64): {len(combined_buffer)} characters")
        
        # Show combined bytes length if available from server
        if 'combined_bytes_length' in audio_data:
            print(f"Combined bytes length (from server): {audio_data['combined_bytes_length']} bytes")
        
        # Decode base64 audio data
        try:
            audio_bytes = base64.b64decode(combined_buffer)
            print(f"Decoded {len(audio_bytes)} bytes of audio data")
        except Exception as e:
            print(f"Error decoding base64 audio: {e}")
            print(f"Buffer sample (first 100 chars): {combined_buffer[:100]}")
            return False
        
        # Convert bytes to numpy array (16-bit PCM LE)
        audio_array = np.frombuffer(audio_bytes, dtype=np.int16)
        
        # Audio quality analysis
        if len(audio_array) > 0:
            max_amplitude = np.max(np.abs(audio_array))
            avg_amplitude = np.mean(np.abs(audio_array))
            non_zero_samples = np.count_nonzero(audio_array)
            
            print(f"Audio analysis:")
            print(f"  Max amplitude: {max_amplitude}")
            print(f"  Average amplitude: {avg_amplitude:.2f}")
            print(f"  Non-zero samples: {non_zero_samples}/{len(audio_array)} ({non_zero_samples/len(audio_array)*100:.1f}%)")
            
            if max_amplitude < 100:
                print("  ⚠️  WARNING: Audio appears to be very quiet or silent!")
        
        # Audio parameters for 16 kHz mono S16LE
        sample_rate = 16000
        channels = 1
        sample_width = 2  # 16-bit = 2 bytes
        
        # Calculate expected vs actual duration
        expected_duration = audio_data.get('last_timestamp', {}).get('relative', 0)
        actual_duration = len(audio_array) / sample_rate
        
        print(f"Duration comparison:")
        print(f"  Expected (from timestamps): {expected_duration:.2f} seconds")
        print(f"  Actual (from audio data): {actual_duration:.2f} seconds")
        
        if abs(expected_duration - actual_duration) > 5:  # More than 5 second difference
            print("  ⚠️  WARNING: Large duration mismatch - possible data loss!")
        
        # Save as WAV file
        with wave.open(output_filename, 'wb') as wav_file:
            wav_file.setnchannels(channels)
            wav_file.setsampwidth(sample_width)
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(audio_bytes)
        
        print(f"✅ Audio saved as '{output_filename}'")
        print(f"Duration: {actual_duration:.2f} seconds")
        print(f"Sample rate: {sample_rate} Hz")
        print(f"Channels: {channels} (mono)")
        print(f"Bit depth: 16-bit")
        
        return True
        
    except requests.exceptions.RequestException as e:
        print(f"HTTP request error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False

def main():
    # Configuration
    BASE_URL = "http://127.0.0.1:8000"  # Updated to match your server
    BOT_ID = input("Enter bot_id: ").strip()
    OUTPUT_FILE = f"meeting_audio_{BOT_ID}.wav"
    
    if not BOT_ID:
        print("Bot ID is required!")
        return
    
    print(f"Fetching audio for bot_id: {BOT_ID}")
    print(f"Server URL: {BASE_URL}")
    
    success = get_and_save_audio(BASE_URL, BOT_ID, OUTPUT_FILE)
    
    if success:
        print(f"\n🎵 You can now play '{OUTPUT_FILE}' with any audio player!")
    else:
        print("\n❌ Failed to retrieve and save audio")

if __name__ == "__main__":
    main()