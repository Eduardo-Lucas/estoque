import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

@Component({
  selector: 'app-confirmar-email',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './confirmar-email.component.html',
  styleUrl: './confirmar-email.component.css',
})
export class ConfirmarEmailComponent implements OnInit {
  private authService = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  confirmando = true;
  erro = '';

  ngOnInit(): void {
    const uid = this.route.snapshot.paramMap.get('uid') ?? '';
    const token = this.route.snapshot.paramMap.get('token') ?? '';

    this.authService.confirmarEmail(uid, token).subscribe({
      next: () => {
        this.router.navigate(['/produtos']);
      },
      error: (err) => {
        this.confirmando = false;
        this.erro = err.message;
      },
    });
  }
}
