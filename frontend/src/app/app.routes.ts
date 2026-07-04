import { Routes } from '@angular/router';
import { ProdutoListComponent } from './components/produto-list/produto-list.component';
import { ProdutoFormComponent } from './components/produto-form/produto-form.component';
import { ProdutoHistoricoComponent } from './components/produto-historico/produto-historico.component';
import { CategoriaListComponent } from './components/categoria-list/categoria-list.component';
import { CategoriaFormComponent } from './components/categoria-form/categoria-form.component';
import { FornecedorListComponent } from './components/fornecedor-list/fornecedor-list.component';
import { FornecedorFormComponent } from './components/fornecedor-form/fornecedor-form.component';
import { MovimentacaoFormComponent } from './components/movimentacao-form/movimentacao-form.component';
import { LoginComponent } from './components/login/login.component';
import { authGuard } from './guards/auth.guard';

export const routes: Routes = [
  { path: '', redirectTo: 'produtos', pathMatch: 'full' },
  { path: 'login', component: LoginComponent },
  { path: 'produtos', component: ProdutoListComponent, canActivate: [authGuard] },
  { path: 'produtos/novo', component: ProdutoFormComponent, canActivate: [authGuard] },
  { path: 'produtos/:id/editar', component: ProdutoFormComponent, canActivate: [authGuard] },
  { path: 'produtos/:id/historico', component: ProdutoHistoricoComponent, canActivate: [authGuard] },
  { path: 'categorias', component: CategoriaListComponent, canActivate: [authGuard] },
  { path: 'categorias/novo', component: CategoriaFormComponent, canActivate: [authGuard] },
  { path: 'categorias/:id/editar', component: CategoriaFormComponent, canActivate: [authGuard] },
  { path: 'fornecedores', component: FornecedorListComponent, canActivate: [authGuard] },
  { path: 'fornecedores/novo', component: FornecedorFormComponent, canActivate: [authGuard] },
  { path: 'fornecedores/:id/editar', component: FornecedorFormComponent, canActivate: [authGuard] },
  { path: 'movimentacoes', component: MovimentacaoFormComponent, canActivate: [authGuard] },
  { path: '**', redirectTo: 'produtos' },
];
