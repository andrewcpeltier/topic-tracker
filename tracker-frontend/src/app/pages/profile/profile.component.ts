import { Component, OnInit, inject, signal } from '@angular/core';
import { FormsModule } from '@angular/forms';

import { ApiService } from '../../services/api.service';

@Component({
  selector: 'app-profile',
  imports: [FormsModule],
  template: `
    <h1>My goals</h1>
    <p class="muted">
      The summarizer reads this before every resource and explains how it relates to these goals.
      New summaries use the updated text; existing ones keep their original explanation.
    </p>
    <div class="card">
      <textarea rows="12" [(ngModel)]="goals" aria-label="Career goals"></textarea>
      <div class="actions">
        <button class="primary" (click)="save()">Save</button>
        <span class="muted">{{ status() }}</span>
      </div>
    </div>
  `,
  styles: `
    textarea { width: 100%; resize: vertical; }
    .actions { display: flex; gap: 1rem; align-items: center; margin-top: 0.75rem; }
  `,
})
export class ProfileComponent implements OnInit {
  private api = inject(ApiService);
  goals = '';
  status = signal('');

  ngOnInit(): void {
    this.api.profile().subscribe((p) => (this.goals = p.goals));
  }

  save(): void {
    this.api.saveProfile(this.goals).subscribe({
      next: () => this.status.set('Saved.'),
      error: () => this.status.set('Could not save.'),
    });
  }
}
