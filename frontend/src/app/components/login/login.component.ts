import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ReactiveFormsModule, FormBuilder, Validators } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-login',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './login.component.html',
  styleUrl: './login.component.css',
})
export class LoginComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);
  private router = inject(Router);

  erro = '';
  carregando = false;
  senhaVisivel = false;

  form = this.fb.nonNullable.group({
    email: ['', [Validators.required, Validators.email]],
    password: ['', Validators.required],
  });

  alternarVisibilidadeSenha(): void {
    this.senhaVisivel = !this.senhaVisivel;
  }

  entrar(): void {
    this.erro = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    this.carregando = true;
    this.authService.login(this.form.getRawValue()).subscribe({
      next: () => {
        this.carregando = false;
        this.router.navigate(['/produtos']);
      },
      error: (err) => {
        this.carregando = false;
        this.erro = err.message;
      },
    });
  }
}
