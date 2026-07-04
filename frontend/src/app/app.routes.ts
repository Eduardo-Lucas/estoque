import { Routes } from '@angular/router';
import { ProdutoListComponent } from './components/produto-list/produto-list.component';
import { MovimentacaoFormComponent } from './components/movimentacao-form/movimentacao-form.component';
import { LoginComponent } from './components/login/login.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'produtos', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'produtos', component: ProdutoListComponent, canActivate: [authGuard] },
  { path: 'movimentacoes', component: MovimentacaoFormComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'produtos' },
];
