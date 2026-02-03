import axios from 'axios';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

api.interceptors.request.use((config) => {
  config.headers['X-Tenant-ID'] = 'demo-cafe';
  return config;
});

api.interceptors.request.use(
  (config) => {
    console.log(`[API REQUEST] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    console.error('[API REQUEST ERROR]', error);
    return Promise.reject(error);
  }
);

api.interceptors.response.use(
  (response) => {
    console.log(`[API RESPONSE] ${response.status} ${response.config.url}`);
    return response;
  },
  (error) => {
    const errorDetail = error.response?.data?.detail || error.response?.data || error.message;
    console.error('[API ERROR]', {
      url: error.config?.url,
      status: error.response?.status,
      detail: errorDetail,
    });
    
    // Debug alert for connection issues (temporary)
    if (!error.response) {
      alert('Connection Error: Backend may be down. Check terminal for details.');
    } else if (error.response.status >= 500) {
      alert(`Server Error (${error.response.status}): ${errorDetail}`);
    }
    
    return Promise.reject(error);
  }
);

export interface UploadResponse {
  status: string;
  file_id: string;
  filename: string;
  message: string;
}

export interface FileStatus {
  file_id: string;
  filename: string;
  status: 'queued' | 'processing' | 'completed' | 'failed';
  ai_detection: string | null;
  rows_processed: number;
  events_mapped: number;
  upload_time: string;
  completed_time: string | null;
  error: string | null;
}

export const uploadFile = async (file: File): Promise<UploadResponse> => {
  const formData = new FormData();
  formData.append('file', file);

  const response = await api.post<UploadResponse>('/ingest/file', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  });
  return response.data;
};

export const getFileStatus = async (): Promise<FileStatus[]> => {
  const response = await api.get<FileStatus[]>('/ingest/status');
  return response.data;
};

export const askQuestion = async (question: string): Promise<string> => {
  const response = await api.post('/query/ask', { question });
  return response.data.answer || response.data.response || JSON.stringify(response.data);
};

export const resetData = async (): Promise<{ message: string }> => {
  const response = await api.post('/master/reset');
  return response.data;
};

export default api;
