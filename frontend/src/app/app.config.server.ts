import { ApplicationConfig, mergeApplicationConfig } from '@angular/core';
import { provideServerRendering } from '@angular/platform-server';
import { provideRouter, withComponentInputBinding, withInMemoryScrolling } from '@angular/router';
import { appConfig } from './app.config';
import { HomeComponent } from './home/home.component';

// First define your server routes
const serverRoutes = [
  {
    path: '',
    component: HomeComponent,
  },
  { path: '**', redirectTo: '' }
];

const serverConfig: ApplicationConfig = {
  providers: [
    provideServerRendering(),
    provideRouter(serverRoutes, withInMemoryScrolling(), withComponentInputBinding())
  ]
};

export const config = mergeApplicationConfig(appConfig, serverConfig);