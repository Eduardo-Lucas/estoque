import { TestBed, ComponentFixture } from '@angular/core/testing';
import { provideRouter } from '@angular/router';
import { of, throwError } from 'rxjs';
import { RegistroComponent } from './registro.component';
import { AuthService } from '../../services/auth.service';

describe('RegistroComponent', () => {
  let fixture: ComponentFixture<RegistroComponent>;
  let component: RegistroComponent;
  let authService: { registrar: jest.Mock };

  const dadosValidos = {
    nome: 'Fulana',
    email: 'fulana@empresa.com',
    password: 'senha-forte-123',
    confirmarPassword: 'senha-forte-123',
    empresaRazaoSocial: 'Empresa Nova LTDA',
    empresaNomeFantasia: '',
    empresaCnpj: '11222333000144',
  };

  beforeEach(async () => {
    authService = { registrar: jest.fn() };

    await TestBed.configureTestingModule({
      imports: [RegistroComponent],
      providers: [provideRouter([]), { provide: AuthService, useValue: authService }],
    }).compileComponents();

    fixture = TestBed.createComponent(RegistroComponent);
    component = fixture.componentInstance;
    fixture.detectChanges();
  });

  it('não chama o serviço e marca os campos como tocados quando o form é inválido', () => {
    component.cadastrar();

    expect(authService.registrar).not.toHaveBeenCalled();
    expect(component.form.get('email')?.touched).toBe(true);
    expect(component.form.get('empresaRazaoSocial')?.touched).toBe(true);
  });

  it('acusa senhas diferentes sem chamar o serviço', () => {
    component.form.setValue({ ...dadosValidos, confirmarPassword: 'outra-senha' });

    component.cadastrar();

    expect(authService.registrar).not.toHaveBeenCalled();
    expect(component.form.hasError('senhasDiferentes')).toBe(true);
  });

  it('cadastro bem-sucedido mostra a mensagem de confirmação pendente', () => {
    authService.registrar.mockReturnValue(of({ detail: 'Cadastro realizado.' }));
    component.form.setValue(dadosValidos);

    component.cadastrar();

    expect(authService.registrar).toHaveBeenCalledWith({
      nome: 'Fulana',
      email: 'fulana@empresa.com',
      password: 'senha-forte-123',
      empresa_razao_social: 'Empresa Nova LTDA',
      empresa_nome_fantasia: undefined,
      empresa_cnpj: '11222333000144',
    });
    expect(component.carregando).toBe(false);
    expect(component.cadastroConcluido).toBe(true);
  });

  it('cadastro com erro exibe a mensagem e não conclui', () => {
    authService.registrar.mockReturnValue(throwError(() => new Error('Já existe uma conta com este e-mail.')));
    component.form.setValue(dadosValidos);

    component.cadastrar();

    expect(component.erro).toBe('Já existe uma conta com este e-mail.');
    expect(component.carregando).toBe(false);
    expect(component.cadastroConcluido).toBe(false);
  });

  it('alterna a visibilidade da senha', () => {
    expect(component.senhaVisivel).toBe(false);
    component.alternarVisibilidadeSenha();
    expect(component.senhaVisivel).toBe(true);
  });
});
