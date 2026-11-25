import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService, Topic } from '../../services/api.service';

interface Draft {
  id?: number;
  name: string;
  description: string;
  queriesText: string;
  sources: Record<string, boolean>;
  enabled: boolean;
}

@Component({
  selector: 'app-topics',
  imports: [FormsModule],
  templateUrl: './topics.component.html',
  styleUrl: './topics.component.scss',
})
export class TopicsComponent implements OnInit {
  private api = inject(ApiService);

  topics = signal<Topic[]>([]);
  sources = signal<string[]>([]);
  draft = signal<Draft | null>(null);
  error = signal('');

  ngOnInit(): void {
    this.api.sources().subscribe((s) => this.sources.set(s));
    this.load();
  }

  load(): void {
    this.api.topics().subscribe((t) => this.topics.set(t));
  }

  edit(topic?: Topic): void {
    this.error.set('');
    const chosen = new Set(topic?.sources ?? this.sources());
    this.draft.set({
      id: topic?.id,
      name: topic?.name ?? '',
      description: topic?.description ?? '',
      queriesText: (topic?.queries ?? []).join('\n'),
      sources: Object.fromEntries(this.sources().map((s) => [s, chosen.has(s)])),
      enabled: topic ? !!topic.enabled : true,
    });
  }

  save(d: Draft): void {
    const topic: Topic = {
      id: d.id,
      name: d.name.trim(),
      description: d.description.trim(),
      queries: d.queriesText.split('\n').map((q) => q.trim()).filter(Boolean),
      sources: Object.keys(d.sources).filter((s) => d.sources[s]),
      enabled: d.enabled,
    };
    if (!topic.name || !topic.queries.length || !topic.sources.length) {
      this.error.set('A topic needs a name, at least one search query and one source.');
      return;
    }
    this.api.saveTopic(topic).subscribe({
      next: () => {
        this.draft.set(null);
        this.load();
      },
      error: (e) => this.error.set(e.error?.detail?.toString?.() ?? 'Could not save the topic.'),
    });
  }

  remove(topic: Topic): void {
    if (topic.id && confirm(`Delete "${topic.name}" and its ${topic.item_count ?? 0} items?`)) {
      this.api.deleteTopic(topic.id).subscribe(() => this.load());
    }
  }
}
