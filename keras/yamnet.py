import tensorflow as tf
import tensorflow_hub as hub
import librosa
import numpy as np

# YAMNet 모델 로드
yamnet_model_handle = "https://tfhub.dev/google/yamnet/1"
yamnet_model = hub.load(yamnet_model_handle)

# 테스트할 오디오 파일 경로
audio_file_path = '/home/rasp/venv/gist-aiot/code/output_channel_1.wav'

# 오디오 파일 로드 및 전처리
def load_audio(file_path, sample_rate=16000):
    # librosa로 오디오 파일 로드
    audio_data, _ = librosa.load(file_path, sr=sample_rate)
    return audio_data

audio_data = load_audio(audio_file_path)

# YAMNet 모델로 예측 수행
scores, embeddings, spectrogram = yamnet_model(audio_data)

# 예측 결과에서 상위 클래스 확인
class_map_path = yamnet_model.class_map_path().numpy().decode('utf-8')
class_names = [name.decode('utf-8') for name in open(class_map_path).readlines()]
top_class_index = tf.argmax(tf.reduce_mean(scores, axis=0)).numpy()
print("Predicted class:", class_names[top_class_index].strip())
