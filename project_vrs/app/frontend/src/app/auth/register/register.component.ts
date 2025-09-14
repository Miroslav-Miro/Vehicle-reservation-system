import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../auth.service';
import { RouterLink } from '@angular/router';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule,RouterLink],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.less']
})
export class RegisterComponent {
  username = '';
  email = '';
  password = '';
  confirmPassword = '';
  first_name = '';
  last_name = '';
  address = '';
  date_of_birth = '';
  phone_number = '';
  error = '';
  success = '';

  constructor(private auth: AuthService, private router: Router) {}

  onSubmit() {
    if (this.password !== this.confirmPassword) {
      this.error = 'Passwords do not match!';
      this.success = '';
      return;
    }

    const payload = {
      username: this.username,
      email: this.email,
      password: this.password,
      first_name: this.first_name,
      last_name: this.last_name,
      address: this.address,
      date_of_birth: this.date_of_birth,
      phone_number: this.phone_number
    };

    this.auth.register(payload).subscribe({
      next: (res) => {
        console.log('Register success:', res);
        this.error = '';
        this.success = 'Account created successfully! You can now log in.';
        // Optionally redirect:
        // this.router.navigate(['/auth/login']);
      },
      error: (err) => {
        console.error('Register failed:', err);
        this.success = '';
        this.error = 'Registration failed. Please check your inputs.';
      }
    });
  }
}
