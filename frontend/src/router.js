import { createRouter, createWebHistory } from 'vue-router';
import TabelaOperadoras from './components/TabelaOperadoras.vue';
import Dashboard from './components/Dashboard.vue';
import DetalhesOperadora from './components/DetalhesOperadora.vue';

const routes = [
  { path: '/', component: TabelaOperadoras },
  { path: '/dashboard', component: Dashboard },
  { path: '/operadora/:id', component: DetalhesOperadora }
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;