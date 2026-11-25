import { HttpClient, HttpParams } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

export interface Item {
  id: number;
  topic_id: number;
  topic_name: string;
  source: string;
  url: string;
  title: string;
  published: string | null;
  summary: string | null;
  relevance: string | null;
  application_ideas: string[];
  relevance_score: number | null;
  saved: number;
  is_read: number;
  created_at: string;
}

export interface Topic {
  id?: number;
  name: string;
  description: string;
  queries: string[];
  sources: string[];
  enabled: boolean | number;
  item_count?: number;
}

export interface ItemFilter {
  topic_id?: number | null;
  min_score?: number;
  saved?: boolean | null;
  unread?: boolean;
  q?: string;
}

export interface RefreshResult {
  fetched: number;
  added: number;
  summarized: number;
  errors: string[];
}

export interface RefreshStatus {
  running: boolean;
  phase: 'idle' | 'starting' | 'fetching' | 'summarizing';
  started_at: string | null;
  finished_at: string | null;
  last_result: RefreshResult | null;
  pending: number;
  summarizer: 'claude_code' | 'openai' | 'stub';
}

@Injectable({ providedIn: 'root' })
export class ApiService {
  private http = inject(HttpClient);
  private base = '/api/v1';

  items(filter: ItemFilter): Observable<Item[]> {
    let params = new HttpParams();
    for (const [key, value] of Object.entries(filter)) {
      if (value !== null && value !== undefined && value !== '' && value !== false) {
        params = params.set(key, String(value));
      }
    }
    return this.http.get<Item[]>(`${this.base}/items`, { params });
  }

  updateItem(id: number, change: { saved?: boolean; is_read?: boolean }): Observable<Item> {
    return this.http.patch<Item>(`${this.base}/items/${id}`, change);
  }

  topics(): Observable<Topic[]> {
    return this.http.get<Topic[]>(`${this.base}/topics`);
  }

  sources(): Observable<string[]> {
    return this.http.get<string[]>(`${this.base}/topics/sources`);
  }

  saveTopic(topic: Topic): Observable<Topic> {
    return topic.id
      ? this.http.put<Topic>(`${this.base}/topics/${topic.id}`, topic)
      : this.http.post<Topic>(`${this.base}/topics`, topic);
  }

  deleteTopic(id: number): Observable<void> {
    return this.http.delete<void>(`${this.base}/topics/${id}`);
  }

  profile(): Observable<{ goals: string }> {
    return this.http.get<{ goals: string }>(`${this.base}/profile`);
  }

  saveProfile(goals: string): Observable<{ goals: string }> {
    return this.http.put<{ goals: string }>(`${this.base}/profile`, { goals });
  }

  /** Starts a background refresh; fetch=false only summarizes items already waiting. */
  refresh(topicId?: number | null, fetch = true): Observable<RefreshStatus> {
    let params = new HttpParams().set('fetch', fetch);
    if (topicId) params = params.set('topic_id', topicId);
    return this.http.post<RefreshStatus>(`${this.base}/refresh`, null, { params });
  }

  status(): Observable<RefreshStatus> {
    return this.http.get<RefreshStatus>(`${this.base}/status`);
  }
}
