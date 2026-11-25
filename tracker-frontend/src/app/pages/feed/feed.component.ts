import { DatePipe } from '@angular/common';
import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService, Item, ItemFilter, Topic } from '../../services/api.service';

@Component({
  selector: 'app-feed',
  imports: [FormsModule, DatePipe],
  templateUrl: './feed.component.html',
  styleUrl: './feed.component.scss',
})
export class FeedComponent implements OnInit {
  private api = inject(ApiService);

  items = signal<Item[]>([]);
  topics = signal<Topic[]>([]);
  loading = signal(false);
  refreshing = signal(false);
  message = signal('');
  filter: ItemFilter = { topic_id: null, min_score: 3, saved: null, unread: false, q: '' };

  readonly sourceLabels: Record<string, string> = {
    arxiv: 'arXiv',
    pubmed: 'PubMed',
    news: 'News',
  };

  ngOnInit(): void {
    this.api.topics().subscribe((t) => this.topics.set(t));
    this.load();
  }

  load(): void {
    this.loading.set(true);
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

  refresh(): void {
    this.refreshing.set(true);
    this.message.set('Fetching and summarizing new resources… this can take a minute or two.');
    this.api.refresh(this.filter.topic_id ?? undefined).subscribe({
      next: (r) => {
        this.refreshing.set(false);
        const errors = r.errors.length ? ` (${r.errors.length} source errors)` : '';
        this.message.set(`Checked ${r.fetched} resources, added ${r.added} new${errors}.`);
        this.load();
      },
      error: (e) => {
        this.refreshing.set(false);
        this.message.set(e.status === 409 ? 'A refresh is already running.' : 'Refresh failed.');
      },
    });
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
