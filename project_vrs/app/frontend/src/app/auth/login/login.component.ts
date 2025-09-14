import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';
import { RouterLink } from '@angular/router';
@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, FormsModule,RouterLink],
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.less']
})
export class LoginComponent {
    username = '';
  password = '';
  error = '';

  constructor(private auth: AuthService, private router: Router) {}

  onSubmit() {
    this.error = '';

    this.auth.login(this.username, this.password).subscribe({
      next: (res: any) => {
        console.log('Login success:', res);

        const role = res.role || 'user';

        // Redirect based on role
        if (role === 'admin') {
          this.router.navigate(['/admin']);
        } else if (role === 'manager') {
          this.router.navigate(['/manager']);
        } else {
          this.router.navigate(['/']);
        }
      },
      error: (err:any) => {
        console.error('Login failed:', err);
        this.error = 'Invalid username or password';
      }
    });
  }
}
