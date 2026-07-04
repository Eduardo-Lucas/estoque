import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { Router, RouterLink, RouterLinkActive, RouterOutlet } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, RouterLink, RouterLinkActive, RouterOutlet],
  templateUrl: './app.component.html',
  styleUrl: './app.component.css',
})
export class AppComponent {
  private authService = inject(AuthService);
  private router = inject(Router);

  titulo = 'Controle de Estoque';
  autenticado = this.authService.autenticado;
  usuario = this.authService.usuario;

  sair(): void {
    this.authService.logout();
    this.router.navigate(['/login']);
  }
}
