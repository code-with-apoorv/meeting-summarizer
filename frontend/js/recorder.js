/**
 * Audio Recorder & Visualizer Module
 */
class MeetingAudioRecorder {
  constructor() {
    this.mediaRecorder = null;
    this.audioChunks = [];
    this.audioBlob = null;
    this.isRecording = false;
    this.isPaused = false;
    this.timerInterval = null;
    this.secondsElapsed = 0;
    this.audioContext = null;
    this.analyser = null;
    this.animationFrameId = null;
    this.canvas = null;
    this.canvasCtx = null;
  }

  initVisualizer(canvasElement) {
    this.canvas = canvasElement;
    if (this.canvas) {
      this.canvasCtx = this.canvas.getContext('2d');
    }
  }

  async startRecording(onTimerUpdate) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.audioChunks = [];
      this.secondsElapsed = 0;

      // Audio context for visualizer
      this.audioContext = new (window.AudioContext || window.webkitAudioContext)();
      const source = this.audioContext.createMediaStreamSource(stream);
      this.analyser = this.audioContext.createAnalyser();
      this.analyser.fftSize = 256;
      source.connect(this.analyser);

      this.mediaRecorder = new MediaRecorder(stream);

      this.mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          this.audioChunks.push(event.data);
        }
      };

      this.mediaRecorder.start(200);
      this.isRecording = true;
      this.isPaused = false;

      // Start timer
      this.timerInterval = setInterval(() => {
        if (!this.isPaused) {
          this.secondsElapsed++;
          if (onTimerUpdate) {
            onTimerUpdate(this.formatTime(this.secondsElapsed));
          }
        }
      }, 1000);

      this.drawWaveform();
      return true;
    } catch (err) {
      console.error('Error accessing microphone:', err);
      throw err;
    }
  }

  stopRecording() {
    return new Promise((resolve) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
        resolve(null);
        return;
      }

      this.mediaRecorder.onstop = () => {
        this.audioBlob = new Blob(this.audioChunks, { type: 'audio/webm' });
        // Stop audio tracks
        if (this.mediaRecorder.stream) {
          this.mediaRecorder.stream.getTracks().forEach((track) => track.stop());
        }
        if (this.audioContext && this.audioContext.state !== 'closed') {
          this.audioContext.close();
        }
        clearInterval(this.timerInterval);
        cancelAnimationFrame(this.animationFrameId);
        this.isRecording = false;
        this.clearCanvas();

        const file = new File([this.audioBlob], `mic_recording_${Date.now()}.webm`, {
          type: 'audio/webm',
        });
        resolve({ blob: this.audioBlob, file: file, duration: this.secondsElapsed });
      };

      this.mediaRecorder.stop();
    });
  }

  drawWaveform() {
    if (!this.canvas || !this.analyser) return;

    const bufferLength = this.analyser.frequencyBinCount;
    const dataArray = new Uint8Array(bufferLength);

    const renderFrame = () => {
      if (!this.isRecording) return;
      this.animationFrameId = requestAnimationFrame(renderFrame);

      this.analyser.getByteFrequencyData(dataArray);

      const width = this.canvas.width;
      const height = this.canvas.height;
      this.canvasCtx.clearRect(0, 0, width, height);

      const barWidth = (width / bufferLength) * 2.5;
      let barHeight;
      let x = 0;

      for (let i = 0; i < bufferLength; i++) {
        barHeight = (dataArray[i] / 255) * height;

        const gradient = this.canvasCtx.createLinearGradient(0, height, 0, 0);
        gradient.addColorStop(0, '#3B82F6');
        gradient.addColorStop(1, '#60A5FA');

        this.canvasCtx.fillStyle = gradient;
        this.canvasCtx.fillRect(x, height - barHeight, barWidth - 1, barHeight);

        x += barWidth + 1;
      }
    };

    renderFrame();
  }

  clearCanvas() {
    if (this.canvas && this.canvasCtx) {
      this.canvasCtx.clearRect(0, 0, this.canvas.width, this.canvas.height);
    }
  }

  formatTime(seconds) {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
  }
}

window.meetingRecorder = new MeetingAudioRecorder();
