import { CommonModule } from '@angular/common';
import { HttpClient, HttpErrorResponse } from '@angular/common/http'; // ✅ Keep this for DI
import { Component, OnInit } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
@Component({
  selector: 'app-home',
  standalone: true,  
  imports: [CommonModule, FormsModule],  // ✅ Removed `Router`
  templateUrl: './home.component.html',
  styleUrls: ['./home.component.css']
})
export class HomeComponent implements OnInit {
  events: string[] = [];
  freeTimeFrom: string = '09:00 AM';  // Default "From" time
  freeTimeTo: string = '05:00 PM';    // Default "To" time
  scheduleResult: any;
  isGoogleConnected = false;
  newEvent: string = '';
  
  timeOptions: string[] = [
    '08:00 AM', '09:00 AM', '10:00 AM', '11:00 AM', '12:00 PM',
    '01:00 PM', '02:00 PM', '03:00 PM', '04:00 PM', '05:00 PM',
    '06:00 PM', '07:00 PM', '08:00 PM', '09:00 PM', '10:00 PM', '11:00 PM', '12:00 AM',
    '01:00 AM', '02:00 AM', '03:00 AM', '04:00 AM', '05:00 AM',
    '06:00 AM', '07:00 AM'
  ];


  constructor(private http: HttpClient, private router: Router) {}

  addEvent(eventValue: string) {
    if (eventValue.trim()) {
      this.events.push(eventValue.trim());
    }
  }
  
  

  removeEvent(index: number) {
    this.events.splice(index, 1);
  }

  connectGoogle() {
    window.location.href = 'http://localhost:8000/auth/google';
  }
  isLoading = false;
  generateSchedule() {
    if (this.events.length === 0) {
      alert('Please add at least one event');
      return;
    }

    this.isLoading = true;
  
    const formattedEvents = this.events.map(event => ({ event_name: event }));
    const freeTime = [{ start: this.freeTimeFrom, end: this.freeTimeTo }];
  
    const apiUrl = 'http://localhost:8000/generate_schedule';
    console.log('Input being sent to backend:', { 
      user_events: formattedEvents, 
      free_time: freeTime 
    });
    // Explicitly type the response as { schedule: string }
    this.http.post<{ schedule: string }>(apiUrl, {
      user_events: formattedEvents,
      free_time: freeTime
    }, { withCredentials: true }).subscribe({
      next: (response) => {
        if (!response.schedule) {
          throw new Error('Backend returned invalid schedule format');
        }
        console.log('Backend response:', response.schedule);
        this.scheduleResult = response.schedule; // Store the string
      },
      error: (err: HttpErrorResponse) => {
        if (err.status === 0) {
          alert('Cannot connect to backend. Please:\n1. Ensure FastAPI is running\n2. Check CORS settings');
        } else {
          // Handle structured errors (from FastAPI's HTTPException)
          const errorDetail = err.error?.detail || 'Schedule generation failed';
          alert(typeof errorDetail === 'object' ? JSON.stringify(errorDetail) : errorDetail);
        }
      },
      complete: () => {
        this.isLoading = false; // Reset loading state when done
      }
    });
  }
 

  // Add this to your component class
syncCompleted = false;

syncWithGoogle() {
  if (!this.scheduleResult) return;
  
  // Structure the data to match what the backend expects
  const requestData = {
    schedule: this.scheduleResult
  };
  
  console.log('Stringified requestData:', JSON.stringify(requestData));
  
  this.http.post(
    'http://localhost:8000/generate_and_sync', 
    requestData, 
    {
      withCredentials: true,
      headers: { 'Content-Type': 'application/json' }
    }
  ).subscribe({
    next: (response) => {
      console.log('[4/5] Sync successful:', response);
      this.syncCompleted = true; // Set sync as completed
      
      // Reset the status after 3 seconds (optional)
      setTimeout(() => {
        this.syncCompleted = false;
      }, 3000);
      
      if (response && 'schedule' in response) {
        console.log('[5/5] Parsed events from backend:', response['schedule']);
      } else {
        console.warn('[5/5] Warning: No schedule received from backend.');
      }
    },
    error: (err) => {
      console.error('[ERROR] Request failed:', {
        status: err.status,
        message: err.message,
        url: err.url,
        headers: err.headers,
        error: err.error
      });
      this.syncCompleted = false;
    }
  });
}
  checkGoogleAuth() {
    this.http.get('http://localhost:8000/auth/check', { withCredentials: true })
      .subscribe({
        next: () => this.isGoogleConnected = true,
        error: () => this.isGoogleConnected = false
      });
  }

  ngOnInit() {
    this.checkGoogleAuth();
  }
}
