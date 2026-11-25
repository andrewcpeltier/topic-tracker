import { DatePipe } from '@angular/common';
import { Component, OnDestroy, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService, Item, ItemFilter, RefreshStatus, Topic } from '../../services/api.service';

@Component({
  selector: 'app-feed',
  imports: [FormsModule, DatePipe],
  templateUrl: './feed.component.html',
  styleUrl: './feed.component.scss',
})
export class FeedComponent implements OnInit, OnDestroy {
  private api = inject(ApiService);

  items = signal<Item[]>([]);
  topics = signal<Topic[]>([]);
  loading = signal(false);
  refreshing = signal(false);
  message = signal('');
  status = signal<RefreshStatus | null>(null);
  private poll?: ReturnType<typeof setTimeout>;
  filter: ItemFilter = { topic_id: null, min_score: 3, saved: null, unread: false, q: '' };

  readonly sourceLabels: Record<string, string> = {
    arxiv: 'arXiv',
    pubmed: 'PubMed',
    news: 'News',
  };

  ngOnInit(): void {
    this.api.topics().subscribe((t) => this.topics.set(t));
    this.load();
    this.api.status().subscribe((s) => (s.running ? this.track(s) : this.status.set(s)));
  }

  load(showSpinner = true): void {
    if (showSpinner) this.loading.set(true);
    this.api.items(this.filter).subscribe({
      next: (items) => {
        this.items.set(items);
        this.loading.set(false);
      },
      error: () => {
        this.message.set('Could not reach the API. Is tracker-api running on port 8000?');
        this.loading.set(false);
      },
    });
  }

  refresh(fetch = true): void {
    this.api.refresh(this.filter.topic_id, fetch).subscribe({
      next: (s) => this.track(s),
      error: (e) => {
        if (e.status === 409) {
          this.api.status().subscribe((s) => this.track(s)); // follow the run already going
        } else {
          this.message.set('Could not start a refresh.');
        }
      },
    });
  }

  /** Follow a background refresh until it finishes, reloading the feed as summaries land. */
  private track(s: RefreshStatus): void {
    this.status.set(s);
    this.refreshing.set(s.running);
    if (s.running) {
      const r = s.last_result;
      this.message.set(
        s.phase === 'summarizing'
          ? `Summarizing with ${this.backendLabel(s)}… ${r?.summarized ?? 0} done, ` +
              `${s.pending} waiting. This can take a few minutes.`
          : 'Fetching new resources…',
      );
      if (s.phase === 'summarizing') this.load(false);
      clearTimeout(this.poll);
      this.poll = setTimeout(() => this.api.status().subscribe((n) => this.track(n)), 4000);
      return;
    }
    const r = s.last_result;
    if (r) {
      const errors = r.errors.length ? ` ${r.errors.length} problem(s): ${r.errors[0]}` : '';
      this.message.set(
        `Done. Added ${r.added} new, summarized ${r.summarized}, ${s.pending} still waiting.${errors}`,
      );
    }
    this.load(false);
  }

  backendLabel(s: RefreshStatus): string {
    return { claude_code: 'Claude Code', openai: 'OpenAI', stub: 'placeholder text' }[s.summarizer];
  }

  ngOnDestroy(): void {
    clearTimeout(this.poll);
  }

  toggleSaved(item: Item): void {
    this.api.updateItem(item.id, { saved: !item.saved }).subscribe((u) => this.replace(u, item));
  }

  markRead(item: Item): void {
    if (!item.is_read) {
      this.api.updateItem(item.id, { is_read: true }).subscribe((u) => this.replace(u, item));
    }
  }

  private replace(updated: Item, old: Item): void {
    this.items.update((list) =>
      list.map((i) => (i.id === updated.id ? { ...updated, topic_name: old.topic_name } : i)),
    );
  }
}
