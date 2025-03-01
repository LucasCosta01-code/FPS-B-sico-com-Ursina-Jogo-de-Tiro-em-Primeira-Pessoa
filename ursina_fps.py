from ursina import *
from ursina.prefabs.first_person_controller import FirstPersonController
import random

# Inicialização da aplicação
app = Ursina()

# Configuração de texturas e sons
try:
    gun_texture = load_texture('assets/gun_texture.png')
    bullet_sound = Audio('assets/shoot.wav', loop=False, autoplay=False)
    enemy_texture = load_texture('assets/enemy.png')
except:
    print("Arquivos de textura/som não encontrados. Usando padrões.")
    gun_texture = None
    bullet_sound = None
    enemy_texture = None

# Configuração do ambiente
Sky()

# Variável para controlar o estado do jogo
game_started = False

# Criação do chão
ground = Entity(
    model='plane',
    texture='grass',
    collider='box',
    scale=(100, 1, 100),
    texture_scale=(30, 30)
)

# Criação das paredes para delimitar a área
wall_1 = Entity(model='cube', collider='box', position=(0, 0, 50), scale=(100, 10, 1), color=color.gray)
wall_2 = Entity(model='cube', collider='box', position=(0, 0, -50), scale=(100, 10, 1), color=color.gray)
wall_3 = Entity(model='cube', collider='box', position=(50, 0, 0), scale=(1, 10, 100), color=color.gray)
wall_4 = Entity(model='cube', collider='box', position=(-50, 0, 0), scale=(1, 10, 100), color=color.gray)

# Adicionando obstáculos
for i in range(20):
    obstacle = Entity(
        model='cube',
        color=color.brown,
        position=(random.uniform(-45, 45), 0.5, random.uniform(-45, 45)),
        scale=(random.uniform(1, 3), random.uniform(1, 5), random.uniform(1, 3)),
        collider='box'
    )

# Função para reiniciar o jogo
def reset_game():
    global game_started, player, title, start_button, exit_button
    
    # Desativar o estado do jogo primeiro
    game_started = False
    
    # Desativar elementos do jogador
    if player:
        player.enabled = False
        if hasattr(player, 'gun'):
            player.gun.enabled = False
        if hasattr(player, 'crosshair'):
            player.crosshair.enabled = False
    
    # Destruir elementos UI existentes
    if hasattr(player, 'health_bar'):
        destroy(player.health_bar)
    if hasattr(player, 'ammo_text'):
        destroy(player.ammo_text)
    if hasattr(player, 'score_text'):
        destroy(player.score_text)
    
    # Remover todos os elementos da tela de game over e efeitos visuais
    for entity in [e for e in scene.entities]:
        if isinstance(entity, Text) and (entity.text == "GAME OVER" or "Pontuação Final" in entity.text):
            destroy(entity)
        if isinstance(entity, Button) and (entity.text == "Reiniciar" or entity.text == "Menu Principal"):
            destroy(entity)
        if isinstance(entity, Entity) and entity.parent == camera.ui:
            destroy(entity)  # Remove todos os elementos UI, incluindo o fade
    
    # Destruir inimigos existentes
    for enemy in [e for e in scene.entities if hasattr(e, 'is_enemy') and e.is_enemy]:
        destroy(enemy)
    
    # Recriar o jogador
    player = Player(position=Vec3(0, 1, 0))
    player.score = 0
    player.health = player.max_health
    player.ammo = player.max_ammo
    
    # Recriar elementos UI do jogador
    player.health_bar = Text(text=f"Vida: {player.health}/{player.max_health}", position=(-0.85, 0.45), scale=1.5, enabled=False)
    player.ammo_text = Text(text=f"Munição: {player.ammo}/{player.max_ammo}", position=(-0.85, 0.4), scale=1.5, enabled=False)
    player.score_text = Text(text=f"Pontuação: {player.score}", position=(-0.85, 0.35), scale=1.5, enabled=False)
    
    # Recriar elementos do menu
    title = Text(text="JOGO FPS", position=(0, 0.3), scale=3, color=color.yellow)
    start_button = Button(text="Iniciar Jogo", position=(0, 0), scale=(0.3, 0.1))
    exit_button = Button(text="Sair", position=(0, -0.15), scale=(0.3, 0.1))
    
    # Configurar ações dos botões
    start_button.on_click = start_game
    exit_button.on_click = exit_game
    
    # Desbloquear o mouse para interagir com o menu
    mouse.locked = False
    
    # Gerar novos inimigos
    for _ in range(10):
        spawn_enemy()
    
    # Garantir que o jogo está em estado ativo
    game_started = True

# Classe para o jogador
class Player(FirstPersonController):
    def __init__(self, **kwargs):
        self.cursor = None  # Initialize cursor as None first
        super().__init__(**kwargs)
        self.health = 100
        self.max_health = 100
        self.ammo = 30
        self.max_ammo = 30
        self.score = 0
        self.sprint_speed = 12  # Sprint speed multiplier
        self.normal_speed = 5   # Normal speed
        self.speed = self.normal_speed  # Current speed
        
        # Desativar o jogador até o jogo começar
        self.enabled = False
        
        # HUD - Interface do usuário
        self.health_bar = Text(text=f"Vida: {self.health}/{self.max_health}", position=(-0.85, 0.45), scale=1.5, enabled=False)
        self.ammo_text = Text(text=f"Munição: {self.ammo}/{self.max_ammo}", position=(-0.85, 0.4), scale=1.5, enabled=False)
        self.score_text = Text(text=f"Pontuação: {self.score}", position=(-0.85, 0.35), scale=1.5, enabled=False)
        
        # Arma
        self.gun = Entity(
            parent=camera.ui,
            model='cube',
            texture=gun_texture,
            position=(0.5, -0.25, 0.5),
            scale=(0.3, 0.2, 1),
            rotation=(0, -5, 0),
            enabled=False
        )
        
        # Mira
        self.crosshair = Entity(
            parent=camera.ui,
            model='quad',
            scale=0.01,
            color=color.white,
            enabled=False
        )
    def update(self):
        if not game_started:
            return
            
        super().update()
        
        # Atualizar HUD
        self.health_bar.text = f"Vida: {self.health}/{self.max_health}"
        self.ammo_text.text = f"Munição: {self.ammo}/{self.max_ammo}"
        self.score_text.text = f"Pontuação: {self.score}"
        
        # Verificar se o jogador morreu
        if self.health <= 0:
            # Desativar controles do jogador
            self.enabled = False
            mouse.locked = False
            
            # Criar efeito de fade out
            fade = Entity(model='quad', color=color.black, scale=2, parent=camera.ui)
            fade.animate_color(color.rgba(0, 0, 0, 0.8), duration=1)
            
            # Mostrar texto de game over com animação
            game_over_text = Text(text="GAME OVER", position=(0, 0.3), scale=0, color=color.red, origin=(0, 0))
            game_over_text.animate_scale(3, duration=1)
            
            # Mostrar pontuação final
            final_score = Text(
                text=f"Pontuação Final: {self.score}",
                position=(0, 0.1),
                scale=2,
                color=color.yellow,
                origin=(0, 0)
            )
            
            # Botões
            restart_button = Button(
                text="Reiniciar",
                position=(0, -0.1),
                scale=(0.2, 0.1),
                color=color.azure
            )
            menu_button = Button(
                text="Menu Principal",
                position=(0, -0.25),
                scale=(0.2, 0.1),
                color=color.azure
            )
            
            # Configurar ações dos botões
            restart_button.on_click = reset_game
            menu_button.on_click = lambda: destroy(menu_button) or reset_game()
            mouse.locked = False
    def input(self, key):
        if not game_started:
            return
            
        super().input(key)
        
        # Sprint control
        if key == 'control':
            self.speed = self.sprint_speed
        if key == 'control up':
            self.speed = self.normal_speed
        
        # Atirar
        if key == 'left mouse down' and self.ammo > 0:
            self.shoot()
        
        # Recarregar
        if key == 'r':
            self.reload()
    
    def shoot(self):
        if self.ammo <= 0:
            return
        
        # Reduzir munição
        self.ammo -= 1
        
        # Efeito sonoro
        if bullet_sound:
            bullet_sound.play()
        
        # Efeito visual de recuo
        self.gun.animate_position((0.5, -0.2, 0.5), duration=0.05, curve=curve.linear)
        self.gun.animate_position((0.5, -0.25, 0.5), duration=0.05, delay=0.05, curve=curve.linear)
        
        # Raycasting para detectar colisões
        hit_info = raycast(camera.world_position, camera.forward, distance=100)
        
        if hit_info.hit:
            # Se atingiu um inimigo
            if hasattr(hit_info.entity, 'is_enemy') and hit_info.entity.is_enemy:
                hit_info.entity.take_damage(25)
                self.score += 10
    
    def reload(self):
        self.ammo = self.max_ammo
        print("Recarregando...")
    
    def take_damage(self, amount):
        self.health -= amount
        # Efeito visual de dano
        camera.shake(duration=0.2, magnitude=0.1)

# Classe para inimigos
class Enemy(Entity):
    def __init__(self, position, **kwargs):
        super().__init__(
            model='cube',
            texture=enemy_texture,
            collider='box',
            position=position,
            scale=(1, 2, 1),
            color=color.red,
            enabled=False,  # Inimigos começam desativados
            **kwargs
        )
        self.health = 100
        self.is_enemy = True
        self.speed = random.uniform(2, 5)
        
        # Barra de vida do inimigo
        self.health_bar = Entity(
            parent=self,
            model='quad',
            color=color.red,
            scale=(1.5, 0.1, 0.1),
            position=(0, 1.2, 0),
            billboard=True
        )
    
    def update(self):
        if not game_started:
            return
            
        # Movimento em direção ao jogador
        if player and distance(self.position, player.position) < 30:
            # Olhar para o jogador apenas no plano horizontal
            target_position = Vec3(player.position.x, self.y, player.position.z)
            self.look_at(target_position)
            
            # Mover em direção ao jogador
            self.position += self.forward * self.speed * time.dt
            
            # Atacar se estiver perto
            if distance(self.position, player.position) < 3:
                player.take_damage(1)
    
    def take_damage(self, amount):
        self.health -= amount
        
        # Atualizar barra de vida
        self.health_bar.scale_x = self.health / 100 * 1.5
        
        # Efeito visual de dano
        self.blink(color.white, duration=0.1)
        
        # Verificar se morreu
        if self.health <= 0:
            self.die()
    
    def die(self):
        # Efeito de explosão
        explosion = Entity(
            model='sphere',
            color=color.yellow,
            position=self.position,
            scale=0.1
        )
        explosion.animate_scale(3, duration=0.3, curve=curve.out_expo)
        explosion.animate_color(color.clear, duration=0.3)
        destroy(explosion, delay=0.3)
        
        # Remover o inimigo
        destroy(self)
        
        # Gerar um novo inimigo em posição aleatória
        spawn_enemy()

# Função para gerar inimigos
def spawn_enemy():
    x = random.uniform(-45, 45)
    z = random.uniform(-45, 45)
    
    # Garantir que o inimigo não apareça muito perto do jogador
    while distance((x, 0, z), player.position) < 10:
        x = random.uniform(-45, 45)
        z = random.uniform(-45, 45)
    
    enemy = Enemy(position=(x, 1, z))
    if game_started:
        enemy.enabled = True
    return enemy

# Criar o jogador
player = Player(position=(0, 1, 0))

# Gerar inimigos iniciais (que estarão desativados)
enemies = []
for _ in range(10):
    x = random.uniform(-45, 45)
    z = random.uniform(-45, 45)
    enemy = Enemy(position=(x, 1, z))
    enemies.append(enemy)

# Função para gerar inimigos periodicamente
def spawn_enemies_periodically():
    if game_started:
        spawn_enemy()
    invoke(spawn_enemies_periodically, delay=5)

# Tela de início
title = Text(text="JOGO FPS", position=(0, 0.3), scale=3, color=color.yellow)
start_button = Button(text="Iniciar Jogo", position=(0, 0), scale=(0.3, 0.1))
exit_button = Button(text="Sair", position=(0, -0.15), scale=(0.3, 0.1))

def start_game():
    global game_started
    
    # Ativar o estado do jogo
    game_started = True
    
    # Esconder elementos do menu
    title.enabled = False
    start_button.enabled = False
    exit_button.enabled = False
    
    # Ativar o jogador e seus elementos
    player.gun.enabled = True
    player.crosshair.enabled = True
    player.health_bar.enabled = True
    player.ammo_text.enabled = True
    player.score_text.enabled = True
    
    # Ativar o jogador por último para garantir que todos os componentes estejam prontos
    player.enabled = True
    
    # Ativar todos os inimigos
    for entity in scene.entities:
        if hasattr(entity, 'is_enemy') and entity.is_enemy:
            entity.enabled = True
    
    # Iniciar geração periódica de inimigos
    invoke(spawn_enemies_periodically, delay=5)
    
    # Ativar controles do mouse
    mouse.locked = True

def exit_game():
    application.quit()

start_button.on_click = start_game
exit_button.on_click = exit_game

# Iniciar o jogo
app.run()