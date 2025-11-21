const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://127.0.0.1:8000';

export interface ProgressEvent {
  stage: string;
  message: string;
  progress: number;
}

export interface CompleteEvent {
  status: string;
  translated_video: string;
  original_language: string;
  target_language: string;
  progress: number;
}

export interface ErrorEvent {
  message: string;
  progress: number;
}

export type SSEEvent = ProgressEvent | CompleteEvent | ErrorEvent;

export async function uploadVideoWithProgress(
  file: File,
  targetLanguage: string,
  selectedVoice: string,
  onProgress: (event: ProgressEvent) => void,
  onComplete: (event: CompleteEvent) => void,
  onError: (event: ErrorEvent) => void
): Promise<void> {
  const formData = new FormData();
  formData.append('file', file);

  const response = await fetch(`${API_BASE_URL}/api/v1/video/upload-stream?target_language=${targetLanguage}&voice=${selectedVoice}`, {
    method: 'POST',
    body: formData,
  });

  if (!response.ok) {
    throw new Error(`Upload failed: ${response.statusText}`);
  }

  const reader = response.body?.getReader();
  const decoder = new TextDecoder();

  if (!reader) {
    throw new Error('No response body');
  }

  let buffer = '';
  let currentEventType = '';

  while (true) {
    const { done, value } = await reader.read();
    
    if (done) break;

    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split('\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('event: ')) {
        currentEventType = line.substring(7).trim();
        continue;
      }

      if (line.startsWith('data: ')) {
        const data = line.substring(6).trim();
        if (!data) continue;
        
        try {
          const parsed = JSON.parse(data);
          
          if (currentEventType === 'complete' || parsed.status === 'success') {
            onComplete(parsed as CompleteEvent);
          } else if (currentEventType === 'error' || (parsed.message && parsed.progress === 0)) {
            onError(parsed as ErrorEvent);
          } else {
            onProgress(parsed as ProgressEvent);
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e, data);
        }
        currentEventType = '';
      }
    }
  }
}

export async function getVoiceLocales() {
    try {
        const response = await fetch(`${API_BASE_URL}/api/v1/video/voices`);

        if (!response.ok) {
            throw new Error(`Upload failed: ${response.statusText}`);
        }

        return await response.json();
    } catch (error) {
        console.error(error);
        throw error;
    }
}

