import { Component, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { AbstractControl, FormBuilder, ReactiveFormsModule, ValidationErrors, Validators } from '@angular/forms';
import { RouterLink } from '@angular/router';
import { AuthService } from '../../services/auth.service';

function senhasIguaisValidator(grupo: AbstractControl): ValidationErrors | null {
  const senha = grupo.get('password')?.value;
  const confirmacao = grupo.get('confirmarPassword')?.value;
  return senha && confirmacao && senha !== confirmacao ? { senhasDiferentes: true } : null;
}

@Component({
  selector: 'app-registro',
  standalone: true,
  imports: [CommonModule, ReactiveFormsModule, RouterLink],
  templateUrl: './registro.component.html',
  styleUrl: './registro.component.css',
})
export class RegistroComponent {
  private fb = inject(FormBuilder);
  private authService = inject(AuthService);

  erro = '';
  carregando = false;
  cadastroConcluido = false;
  senhaVisivel = false;

  form = this.fb.nonNullable.group(
    {
      nome: ['', Validators.required],
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(8)]],
      confirmarPassword: ['', Validators.required],
      empresaRazaoSocial: ['', Validators.required],
      empresaNomeFantasia: [''],
      empresaCnpj: ['', Validators.required],
    },
    { validators: senhasIguaisValidator },
  );

  alternarVisibilidadeSenha(): void {
    this.senhaVisivel = !this.senhaVisivel;
  }

  cadastrar(): void {
    this.erro = '';

    if (this.form.invalid) {
      this.form.markAllAsTouched();
      return;
    }

    const dados = this.form.getRawValue();
    this.carregando = true;
    this.authService
      .registrar({
        nome: dados.nome,
        email: dados.email,
        password: dados.password,
        empresa_razao_social: dados.empresaRazaoSocial,
        empresa_nome_fantasia: dados.empresaNomeFantasia || undefined,
        empresa_cnpj: dados.empresaCnpj,
      })
      .subscribe({
        next: () => {
          this.carregando = false;
          this.cadastroConcluido = true;
        },
        error: (err) => {
          this.carregando = false;
          this.erro = err.message;
        },
      });
  }
}
