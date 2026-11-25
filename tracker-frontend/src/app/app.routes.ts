import { Routes } from '@angular/router';

import { FeedComponent } from './pages/feed/feed.component';
import { ProfileComponent } from './pages/profile/profile.component';
import { TopicsComponent } from './pages/topics/topics.component';

export const routes: Routes = [
  { path: '', component: FeedComponent, title: 'Feed · Topic Tracker' },
  { path: 'topics', component: TopicsComponent, title: 'Topics · Topic Tracker' },
  { path: 'goals', component: ProfileComponent, title: 'Goals · Topic Tracker' },
  { path: '**', redirectTo: '' },
];
