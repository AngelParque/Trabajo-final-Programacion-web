import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

type Item = {
  id: number;
  name: string;
  category: string;
  unit: string;
  stock: number;
  minimum: number;
};
type Activity = { id: number; name: string; date: string; owner: string; status: string };
type Move = {
  id: number;
  item_name: string;
  kind: string;
  quantity: number;
  reason: string;
  created_at: string;
};

@Component({
  selector: 'app-root',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './app.html',
  styleUrl: './app.css',
})
export class App implements OnInit {
  page = signal('inicio');
  items = signal<Item[]>([]);
  activities = signal<Activity[]>([]);
  moves = signal<Move[]>([]);
  message = signal('');
  busy = signal(false);
  query = '';
  itemForm: any = { name: '', category: 'Abarrotes', unit: 'kg', stock: 0, minimum: 1 };
  activityForm: any = { name: '', date: '', owner: 'Coordinación', status: 'Pendiente' };
  moveForm: any = { item_id: 0, kind: 'Entrada', quantity: 1, reason: '' };
  editingItem = 0;
  editingActivity = 0;
  constructor(private http: HttpClient) {}
  ngOnInit() {
    this.refresh();
  }
  refresh() {
    this.http
      .get<Item[]>('/api/items')
      .subscribe({ next: (x) => this.items.set(x), error: () => this.fail() });
    this.http.get<Activity[]>('/api/activities').subscribe((x) => this.activities.set(x));
    this.http.get<Move[]>('/api/movements').subscribe((x) => this.moves.set(x));
  }
  get filtered() {
    const q = this.query.toLowerCase();
    return this.items().filter(
      (x) => x.name.toLowerCase().includes(q) || x.category.toLowerCase().includes(q),
    );
  }
  get lowCount() {
    return this.items().filter((x) => x.stock <= x.minimum).length;
  }
  get totals() {
    return this.items().reduce((s, x) => s + x.stock, 0);
  }
  goto(p: string) {
    this.page.set(p);
    this.message.set('');
  }
  saveItem() {
    this.busy.set(true);
    const req = this.editingItem
      ? this.http.put('/api/items/' + this.editingItem, this.itemForm)
      : this.http.post('/api/items', this.itemForm);
    req.subscribe({
      next: () => {
        this.refresh();
        this.itemForm = { name: '', category: 'Abarrotes', unit: 'kg', stock: 0, minimum: 1 };
        this.editingItem = 0;
        this.ok('Insumo guardado');
      },
      error: (e) => this.fail(e),
      complete: () => this.busy.set(false),
    });
  }
  editItem(x: Item) {
    this.editingItem = x.id;
    this.itemForm = { ...x };
    this.goto('inventario');
  }
  deleteItem(x: Item) {
    if (confirm('¿Eliminar ' + x.name + '?'))
      this.http.delete('/api/items/' + x.id).subscribe({
        next: () => {
          this.refresh();
          this.ok('Insumo eliminado');
        },
        error: (e) => this.fail(e),
      });
  }
  saveActivity() {
    const req = this.editingActivity
      ? this.http.put('/api/activities/' + this.editingActivity, this.activityForm)
      : this.http.post('/api/activities', this.activityForm);
    req.subscribe({
      next: () => {
        this.refresh();
        this.activityForm = { name: '', date: '', owner: 'Coordinación', status: 'Pendiente' };
        this.editingActivity = 0;
        this.ok('Actividad guardada');
      },
      error: (e) => this.fail(e),
    });
  }
  editActivity(a: Activity) {
    this.editingActivity = a.id;
    this.activityForm = { ...a };
  }
  deleteActivity(a: Activity) {
    if (confirm('¿Eliminar esta actividad?'))
      this.http.delete('/api/activities/' + a.id).subscribe({
        next: () => {
          this.refresh();
          this.ok('Actividad eliminada');
        },
        error: (e) => this.fail(e),
      });
  }
  openMove(x: Item) {
    this.moveForm = { item_id: x.id, kind: 'Entrada', quantity: 1, reason: '' };
    this.goto('movimientos');
  }
  saveMove() {
    this.http.post('/api/movements', this.moveForm).subscribe({
      next: () => {
        this.refresh();
        this.ok('Movimiento registrado');
        this.moveForm = { item_id: 0, kind: 'Entrada', quantity: 1, reason: '' };
      },
      error: (e) => this.fail(e),
    });
  }
  resetDemo() {
    if (confirm('Restablecer los datos de demostración?'))
      this.http.post('/api/demo/reset', {}).subscribe({
        next: () => {
          this.refresh();
          this.ok('Datos de ejemplo restablecidos');
        },
        error: (e) => this.fail(e),
      });
  }
  ok(s: string) {
    this.message.set(s);
    setTimeout(() => this.message.set(''), 3000);
  }
  fail(e?: any) {
    this.message.set(
      e?.error?.detail || 'No se pudo conectar con la API. Verifica que el backend esté iniciado.',
    );
    this.busy.set(false);
  }
}
