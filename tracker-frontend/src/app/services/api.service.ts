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
  errors: string[];
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

  refresh(topicId?: number): Observable<RefreshResult> {
    const params = topicId ? new HttpParams().set('topic_id', topicId) : undefined;
    return this.http.post<RefreshResult>(`${this.base}/refresh`, null, { params });
  }
}
