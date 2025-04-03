import { RenderMode, ServerRoute } from '@angular/ssr';
import { HomeComponent } from './home/home.component';
export const serverRoutes: ServerRoute[] = [
  {
    path: '**',
    renderMode: RenderMode.Prerender
  },
  {  path: '',
    component: HomeComponent,
    renderMode: RenderMode.Prerender ,
    data: { preload: true }}, // Home route
];
