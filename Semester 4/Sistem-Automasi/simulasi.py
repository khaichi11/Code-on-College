import pygame
import math
import numpy as np
import time
from collections import deque
import random

# Initialize Pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1200
SCREEN_HEIGHT = 800
FPS = 60

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
BLUE = (0, 100, 255)
RED = (255, 0, 0)
GREEN = (0, 180, 0)
GRAY = (128, 128, 128)
DARK_GRAY = (64, 64, 64)
LIGHT_BLUE = (173, 216, 230)
ORANGE = (255, 165, 0)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
DARK_BROWN = (101, 67, 33)
LIGHT_BROWN = (181, 137, 83)
METAL_GRAY = (180, 180, 190)
DARK_METAL = (80, 80, 90)
WATER_BLUE = (100, 150, 255, 120)
GRAVEL_COLOR = (139, 119, 101)
PLANT_GREEN = (34, 139, 34)

class PIDController:
    """PID Controller for precise DC motor position control."""
    def __init__(self, kp=2.0, ki=0.5, kd=0.1):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0
        self.max_integral = 100

    def calculate(self, setpoint, current_value, dt):
        error = setpoint - current_value
        self.integral += error * dt
        self.integral = max(-self.max_integral, min(self.max_integral, self.integral))
        derivative = (error - self.prev_error) / dt if dt > 0 else 0
        output = (self.kp * error + self.ki * self.integral + self.kd * derivative)
        self.prev_error = error
        return output

    def reset(self):
        self.prev_error = 0
        self.integral = 0

class DCMotor:
    """DC Motor model for precise feeding control."""
    def __init__(self):
        self.voltage = 0.0
        self.current_angle = 0.0
        self.target_angle = 0.0
        self.angular_velocity = 0.0
        self.max_voltage = 12.0
        self.max_angular_velocity = 180.0
        self.resistance = 2.0
        self.inductance = 0.1
        self.torque_constant = 0.15
        self.back_emf_constant = 0.1
        self.friction = 0.1
        self.inertia = 0.02
        self.current = 0.0
        self.is_feeding = False
        self.feed_complete = True
        self.volume_per_rotation = 0.001

    def update(self, voltage, dt):
        self.voltage = max(-self.max_voltage, min(self.max_voltage, voltage))
        back_emf = self.back_emf_constant * (self.angular_velocity / 60.0)
        self.current = (self.voltage - back_emf) / self.resistance
        motor_torque = self.torque_constant * self.current
        friction_torque = self.friction * self.angular_velocity / 100.0
        net_torque = motor_torque - friction_torque
        angular_acceleration = net_torque / self.inertia
        self.angular_velocity += angular_acceleration * dt * 100
        self.angular_velocity = max(-self.max_angular_velocity, min(self.max_angular_velocity, self.angular_velocity))
        self.current_angle += self.angular_velocity * dt

        if self.is_feeding:
            angle_error = abs(self.target_angle - self.current_angle)
            # *** KONDISI FEED_COMPLETE DIPERKETAT ***
            if angle_error < 1.0 and abs(self.angular_velocity) < 2.0:
                self.feed_complete = True
                self.is_feeding = False
                self.angular_velocity = 0 # Pastikan berhenti total

    def start_feeding(self, volume_liters):
        if self.feed_complete:
            required_rotations = volume_liters / self.volume_per_rotation
            required_angle = required_rotations * 360.0
            self.target_angle = self.current_angle + required_angle
            self.is_feeding = True
            self.feed_complete = False
            return required_rotations
        return 0

    def get_rpm(self):
        return abs(self.angular_velocity * 60.0 / 360.0)

class FeedingSystem:
    """Manages feed volume and distribution."""
    def __init__(self):
        self.total_feed_dispensed = 0.0
        self.feed_sessions = 0
        self.current_feed_volume = 0.0
        self.feed_particles = []

    def dispense_feed(self, volume, motor_angle):
        particle_count = max(1, int(volume * 12000))
        for _ in range(min(particle_count, 30)):
            angle_rad = math.radians(motor_angle + np.random.randint(-5, 5))
            particle = {
                'x': 500 + 30 * math.cos(angle_rad) + np.random.randint(-15, 15),
                'y': 360 + 30 * math.sin(angle_rad) + np.random.randint(-5, 5),
                'vx': 1.5 * math.cos(angle_rad) + np.random.uniform(-0.5, 0.5),
                'vy': 1.5 * math.sin(angle_rad) + np.random.uniform(0.5, 1.5),
                'life': 500 + np.random.randint(-50, 150),
                'size': max(1, int(volume * 4000)),
                'color': (np.random.randint(130, 180), np.random.randint(80, 120), np.random.randint(0, 30)),
                'shape': 'circle',
                'settled': False,
                'eaten': False
            }
            self.feed_particles.append(particle)

    def update_particles(self, tank_rect, water_surface_y):
        tank_bottom = tank_rect.bottom - 5

        for particle in self.feed_particles[:]:
            if particle['eaten']:
                try: self.feed_particles.remove(particle)
                except ValueError: pass
                continue

            if not particle['settled']:
                particle['x'] += particle['vx']
                particle['y'] += particle['vy']

                if particle['y'] > water_surface_y:
                     particle['vy'] += 0.08; particle['vx'] *= 0.97; particle['vy'] *= 0.98
                else:
                    particle['vy'] += 0.05; particle['vx'] *= 0.99

                if particle['y'] >= tank_bottom - particle['size']:
                    particle['y'] = tank_bottom - particle['size']
                    particle['vy'] = 0; particle['vx'] = 0
                    particle['settled'] = True; particle['life'] = 5000

                particle['x'] = max(tank_rect.left + 5, min(tank_rect.right - 5, particle['x']))

            particle['life'] -= 1
            if particle['life'] <= 0 and not particle['settled']:
                 try: self.feed_particles.remove(particle)
                 except ValueError: pass

class FishFeederSimulator:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Enhanced Fish Feeder Simulation V7")
        self.clock = pygame.time.Clock()

        self.motor = DCMotor()
        self.pid = PIDController(kp=1.5, ki=0.3, kd=0.05)
        self.feeding_system = FeedingSystem()

        self.running = True
        self.system_active = False

        self.angle_history = deque(maxlen=300)
        self.target_angle_history = deque(maxlen=300)
        self.rpm_history = deque(maxlen=300)
        self.buttons = {}

        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 18)
        self.button_font = pygame.font.Font(None, 20)

        self.last_time = time.time()

        self.motor_shaft_angle = 0
        self.feed_level = 100
        self.water_ripples = []

        self.tank_rect = pygame.Rect(250, 450, 500, 300)
        self.water_surface_y = self.tank_rect.y + 40
        self.num_fish = 7
        self.fish_list = []
        self._initialize_fish()
        self.plants = self._initialize_plants()

    def _initialize_plants(self):
        plants = []
        for _ in range(5):
            base_x = self.tank_rect.x + np.random.randint(10, self.tank_rect.width - 20)
            base_y = self.tank_rect.bottom
            height = np.random.randint(40, 100)
            width = np.random.randint(15, 30)
            plants.append({'rect': pygame.Rect(base_x, base_y - height, width, height),
                           'color': (np.random.randint(20, 50), np.random.randint(100, 160), np.random.randint(20, 50))})
        return plants

    def _initialize_fish(self):
        self.fish_list.clear()
        padding = 10; fish_width = 35; fish_height = 20
        spawnable_width = self.tank_rect.width - fish_width - padding * 2
        spawnable_height = (self.tank_rect.height - (self.water_surface_y - self.tank_rect.y)) - fish_height - padding * 2
        if spawnable_width <= 0: spawnable_width = 1
        if spawnable_height <= 0: spawnable_height = 1

        for i in range(self.num_fish):
            initial_vx = np.random.uniform(0.5, 1.2) * np.random.choice([-1, 1])
            self.fish_list.append({
                'id': i,
                'x': self.tank_rect.x + padding + np.random.randint(spawnable_width),
                'y': self.water_surface_y + padding + np.random.randint(spawnable_height),
                'width': fish_width, 'height': fish_height,
                'vx': initial_vx, 'vy': 0,
                'color': (np.random.randint(230,255), np.random.randint(100,160), np.random.randint(0,60)),
                'target_particle': None, 'state': 'swimming', 'eat_timer': 0,
                'tail_phase': np.random.uniform(0, 2 * math.pi),
                'facing_direction': 1 if initial_vx >= 0 else -1
            })

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    pos = pygame.mouse.get_pos()
                    for name, rect in self.buttons.items():
                        if rect.collidepoint(pos):
                            if name == 'power':
                                self.system_active = not self.system_active
                                if not self.system_active: self.emergency_stop()
                            elif self.system_active and self.motor.feed_complete:
                                if name == 'feed_1ml': self.start_feeding(0.001)
                                elif name == 'feed_5ml': self.start_feeding(0.005)
                                elif name == 'feed_10ml': self.start_feeding(0.01)
                                elif name == 'feed_20ml': self.start_feeding(0.02)
                            if name == 'emergency_stop': self.emergency_stop()
                            elif name == 'reset_system': self.reset_system()
                            elif name == 'pid_tune': self.tune_pid()
                            break

    def start_feeding(self, volume):
        if self.system_active and self.motor.feed_complete:
            rotations = self.motor.start_feeding(volume)
            if rotations > 0:
                self.feeding_system.current_feed_volume = volume
                self.feeding_system.feed_sessions += 1
                self.feed_level = max(0, self.feed_level - volume * 1000)
                self.pid.reset()

    def emergency_stop(self):
        self.motor.is_feeding = False
        self.motor.feed_complete = True
        self.motor.target_angle = self.motor.current_angle
        self.motor.angular_velocity = 0
        self.motor.voltage = 0
        self.pid.reset()

    def reset_system(self):
        self.motor = DCMotor()
        self.pid.reset()
        self.feeding_system = FeedingSystem()
        self.system_active = False
        self.feed_level = 100
        self.water_ripples = []
        self.angle_history.clear(); self.target_angle_history.clear(); self.rpm_history.clear()
        self._initialize_fish()

    def tune_pid(self):
        if self.pid.kp == 1.5: self.pid.kp, self.pid.ki, self.pid.kd = 2.0, 0.5, 0.1
        elif self.pid.kp == 2.0: self.pid.kp, self.pid.ki, self.kd = 1.0, 0.2, 0.03
        else: self.pid.kp, self.pid.ki, self.pid.kd = 1.5, 0.3, 0.05

    def _update_fish_behavior(self):
        search_radius_sq = 250**2; chase_speed_x = 1.8; chase_speed_y = 1.5; eat_distance_sq = 10**2
        available_particles = [p for p in self.feeding_system.feed_particles if not p['eaten'] and p['y'] > self.water_surface_y + 5]

        for fish in self.fish_list:
            fish_center_x = fish['x'] + fish['width'] / 2; fish_center_y = fish['y'] + fish['height'] / 2
            fish['tail_phase'] = (fish['tail_phase'] + 0.6 * abs(fish['vx'])) % (2 * math.pi)

            if fish['eat_timer'] > 0:
                fish['eat_timer'] -= 1
                if fish['eat_timer'] == 0: fish['state'] = 'swimming'
                continue

            if fish['target_particle'] and (fish['target_particle']['eaten'] or fish['target_particle'] not in self.feeding_system.feed_particles):
                 fish['target_particle'] = None; fish['state'] = 'swimming'

            if not fish['target_particle']:
                closest_particle_found = None; min_dist_sq_found = search_radius_sq
                for p in available_particles:
                    is_targeted = any(other_fish['target_particle'] == p for other_fish in self.fish_list)
                    if is_targeted: continue
                    dx = p['x'] - fish_center_x; dy = p['y'] - fish_center_y
                    dist_sq = dx*dx + dy*dy
                    if dist_sq < min_dist_sq_found:
                        min_dist_sq_found = dist_sq; closest_particle_found = p
                if closest_particle_found:
                    fish['target_particle'] = closest_particle_found; fish['state'] = 'chasing'
                else: fish['state'] = 'swimming'

            if fish['state'] == 'chasing' and fish['target_particle']:
                target = fish['target_particle']; dx = target['x'] - fish_center_x; dy = target['y'] - fish_center_y
                dist_sq = dx*dx + dy*dy
                if dist_sq < eat_distance_sq:
                    target['eaten'] = True; fish['state'] = 'eating'; fish['eat_timer'] = 8
                    fish['target_particle'] = None; fish['vx'] = 0; fish['vy'] = 0
                    for f in self.fish_list:
                        if f['target_particle'] == target: f['target_particle'] = None; f['state'] = 'swimming'
                else:
                    dist = math.sqrt(dist_sq) if dist_sq > 0 else 1
                    fish['vx'] = (dx / dist) * chase_speed_x; fish['vy'] = (dy / dist) * chase_speed_y
            elif fish['state'] == 'swimming':
                fish['vy'] = np.sin(time.time() * 1.5 + fish['id']) * 0.4
                if abs(fish['vx']) < 0.3: fish['vx'] = np.random.uniform(0.5, 1.2) * np.random.choice([-1, 1])
                if np.random.random() < 0.01: fish['vx'] *= -1

            if abs(fish['vx']) > 0.1: # Threshold to avoid jittery direction changes
                fish['facing_direction'] = 1 if fish['vx'] > 0 else -1

            fish['x'] += fish['vx']; fish['y'] += fish['vy']
            fish['x'] = max(self.tank_rect.x + 5, min(self.tank_rect.right - fish['width'] - 15, fish['x']))
            fish['y'] = max(self.water_surface_y + 5, min(self.tank_rect.bottom - fish['height'] - 5, fish['y']))
            if fish['x'] <= self.tank_rect.x + 5 or fish['x'] >= self.tank_rect.right - fish['width'] - 15:
                fish['vx'] *= -1; fish['state'] = 'swimming'; fish['target_particle'] = None
                if abs(fish['vx']) > 0.1: fish['facing_direction'] = 1 if fish['vx'] > 0 else -1

    def update_system(self):
        current_time = time.time(); dt = current_time - self.last_time; self.last_time = current_time
        if dt <= 0: dt = 1/FPS
        if dt > 0.1: dt = 0.1

        if self.system_active:
            if self.motor.is_feeding:
                control_signal = self.pid.calculate(self.motor.target_angle, self.motor.current_angle, dt)
                voltage = max(-6, min(6, control_signal))
            else: # Not feeding (either completed or never started while active)
                voltage = 0
                # Apply gentle braking if motor is still spinning slowly
                if abs(self.motor.angular_velocity) > 0.1:
                    voltage = -self.motor.angular_velocity * 0.05 # Dynamic braking
                else:
                    self.motor.angular_velocity = 0 # Ensure it's fully stopped
        else: # System inactive
            voltage = 0; self.motor.angular_velocity *= 0.95 # Decelerate
            if abs(self.motor.angular_velocity) < 0.1: self.motor.angular_velocity = 0

        self.motor.update(voltage, dt); self.motor_shaft_angle = self.motor.current_angle

        if self.motor.is_feeding and abs(self.motor.angular_velocity) > 10:
            current_feed_rate = abs(self.motor.angular_velocity) / 360.0 * self.motor.volume_per_rotation
            if current_feed_rate > 0.00001:
                self.feeding_system.dispense_feed(current_feed_rate * dt * FPS * 1.5, self.motor.current_angle)
                if np.random.random() < 0.3:
                    self.water_ripples.append({'x': 500 + np.random.randint(-15, 15), 'y': self.water_surface_y + np.random.randint(-2, 2), 'radius': 3, 'alpha': 255 })

        self.feeding_system.update_particles(self.tank_rect, self.water_surface_y)
        self._update_fish_behavior()

        for ripple in self.water_ripples[:]:
            ripple['radius'] += 0.8; ripple['alpha'] -= 4
            if ripple['alpha'] <= 0: self.water_ripples.remove(ripple)

        if self.motor.feed_complete and self.feeding_system.current_feed_volume > 0:
            self.feeding_system.total_feed_dispensed += self.feeding_system.current_feed_volume
            self.feeding_system.current_feed_volume = 0

        if self.feed_level <= 5 and not self.motor.is_feeding and self.system_active:
            self.feed_level = min(100, self.feed_level + 0.05)

        if self.system_active or len(self.angle_history) > 0 :
            self.angle_history.append(self.motor.current_angle)
            self.target_angle_history.append(self.motor.target_angle)
            self.rpm_history.append(self.motor.get_rpm())

    def draw_motor_assembly(self):
        center_x, center_y = 500, 350
        hopper_top_y = center_y - 120
        hopper_bottom_y = center_y - 80
        pygame.draw.polygon(self.screen, LIGHT_BROWN, [(center_x - 50, hopper_top_y), (center_x + 50, hopper_top_y), (center_x + 40, hopper_bottom_y), (center_x - 40, hopper_bottom_y)])
        pygame.draw.polygon(self.screen, DARK_BROWN, [(center_x - 50, hopper_top_y), (center_x + 50, hopper_top_y), (center_x + 40, hopper_bottom_y), (center_x - 40, hopper_bottom_y)], 3)

        feed_height_px = int((self.feed_level / 100) * (hopper_bottom_y - (hopper_top_y + 5)))
        if feed_height_px > 0:
            bottom_width_feed = 80 * ((hopper_bottom_y - (hopper_bottom_y - feed_height_px)) / (hopper_bottom_y - hopper_top_y))
            bottom_width_feed = max(0, min(80, bottom_width_feed * 0.9))
            pygame.draw.polygon(self.screen, DARK_BROWN, [
                (center_x - 40 + (80-bottom_width_feed)/2 , hopper_bottom_y - feed_height_px),
                (center_x + 40 - (80-bottom_width_feed)/2 , hopper_bottom_y - feed_height_px),
                (center_x + 38, hopper_bottom_y), (center_x - 38, hopper_bottom_y) ])

        pygame.draw.ellipse(self.screen, METAL_GRAY, (center_x - 60, center_y - 40, 120, 80))
        pygame.draw.ellipse(self.screen, DARK_METAL, (center_x - 60, center_y - 40, 120, 80), 3)
        pygame.draw.rect(self.screen, DARK_METAL, (center_x - 70, center_y - 10, 140, 20))
        pygame.draw.circle(self.screen, METAL_GRAY, (center_x, center_y), 30)
        pygame.draw.circle(self.screen, DARK_METAL, (center_x, center_y), 30, 3)

        shaft_angle_rad = math.radians(self.motor_shaft_angle)
        # Garis poros utama
        pygame.draw.line(self.screen, DARK_METAL, (center_x, center_y), (center_x + 25 * math.cos(shaft_angle_rad), center_y + 25 * math.sin(shaft_angle_rad)), 6) # Lebih tebal

        # Bilah/Penanda Putaran (lebih jelas)
        num_blades = 3
        for i in range(num_blades):
            blade_angle = shaft_angle_rad + i * (2 * math.pi / num_blades)
            start_point = (center_x + 8 * math.cos(blade_angle), center_y + 8 * math.sin(blade_angle))
            
            if i == 0: # Buat satu bilah berbeda/lebih panjang sebagai penanda utama
                end_point = (center_x + 28 * math.cos(blade_angle), center_y + 28 * math.sin(blade_angle))
                pygame.draw.line(self.screen, YELLOW, start_point, end_point, 5) # Kuning dan tebal
            else:
                end_point = (center_x + 22 * math.cos(blade_angle), center_y + 22 * math.sin(blade_angle))
                pygame.draw.line(self.screen, ORANGE, start_point, end_point, 3)


        outlet_y = center_y + 40
        pygame.draw.rect(self.screen, METAL_GRAY, (center_x - 20, outlet_y, 40, 30))
        pygame.draw.rect(self.screen, DARK_METAL, (center_x - 20, outlet_y, 40, 30), 3)
        pygame.draw.rect(self.screen, (50, 50, 50), (center_x - 15, outlet_y + 5, 30, 20))

        status_color = GREEN if self.system_active else RED
        pygame.draw.circle(self.screen, status_color, (center_x + 70, hopper_top_y + 10), 8)
        pygame.draw.circle(self.screen, BLACK, (center_x + 70, hopper_top_y + 10), 8, 1)
        self.screen.blit(self.small_font.render("PWR", True, BLACK), (center_x + 80, hopper_top_y + 5))

        if self.motor.is_feeding:
            pygame.draw.circle(self.screen, YELLOW, (center_x - 70, hopper_top_y + 10), 8)
            self.screen.blit(self.small_font.render("FEED", True, BLACK), (center_x - 95, hopper_top_y + 5))
        pygame.draw.circle(self.screen, BLACK, (center_x - 70, hopper_top_y + 10), 8, 1)

        label = self.font.render("FEEDER UNIT", True, DARK_GRAY)
        self.screen.blit(label, (center_x - label.get_width()//2, outlet_y + 40 ))

    def draw_control_panel(self):
        panel_rect = pygame.Rect(30, 30, 550, 230)
        pygame.draw.rect(self.screen, (230, 230, 230), panel_rect, border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, panel_rect, 3, border_radius=10)
        self.screen.blit(self.font.render("CONTROL PANEL", True, DARK_GRAY), (40, 35))

        self.buttons['power'] = pygame.Rect(50, 70, 100, 40)
        color = GREEN if self.system_active else RED
        pygame.draw.rect(self.screen, color, self.buttons['power'], border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.buttons['power'], 2, border_radius=5)
        text = "SYSTEM ON" if self.system_active else "SYSTEM OFF"
        label = self.button_font.render(text, True, BLACK if self.system_active else WHITE)
        self.screen.blit(label, label.get_rect(center=self.buttons['power'].center))

        button_width = 110; button_height = 40; start_x = 50; y_pos = 125; spacing_x = 23
        feed_labels = ["1ml", "5ml", "10ml", "20ml"]
        for i, label_text in enumerate(feed_labels):
            x_offset = i * (button_width + spacing_x)
            key = f"feed_{label_text}"
            rect = pygame.Rect(start_x + x_offset, y_pos, button_width, button_height)
            self.buttons[key] = rect
            color = LIGHT_BLUE if self.system_active and self.motor.feed_complete else GRAY
            pygame.draw.rect(self.screen, color, rect, border_radius=5)
            pygame.draw.rect(self.screen, BLACK, rect, 2, border_radius=5)
            label = self.button_font.render(f"DISPENSE {label_text}", True, BLACK)
            self.screen.blit(label, label.get_rect(center=rect.center))

        lower_y = 180; btn_w_low = 140; space_low = 45; start_x_low = 50
        self.buttons['emergency_stop'] = pygame.Rect(start_x_low, lower_y, btn_w_low, 40)
        self.buttons['reset_system'] = pygame.Rect(start_x_low + btn_w_low + space_low, lower_y, btn_w_low, 40)
        self.buttons['pid_tune'] = pygame.Rect(start_x_low + 2 * (btn_w_low + space_low), lower_y, btn_w_low, 40)

        pygame.draw.rect(self.screen, RED, self.buttons['emergency_stop'], border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.buttons['emergency_stop'], 2, border_radius=5)
        l1 = self.button_font.render("EMERGENCY STOP", True, WHITE)
        self.screen.blit(l1, l1.get_rect(center=self.buttons['emergency_stop'].center))
        pygame.draw.rect(self.screen, PURPLE, self.buttons['reset_system'], border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.buttons['reset_system'], 2, border_radius=5)
        label = self.button_font.render("RESET SYSTEM", True, WHITE)
        self.screen.blit(label, label.get_rect(center=self.buttons['reset_system'].center))
        pygame.draw.rect(self.screen, LIGHT_BLUE, self.buttons['pid_tune'], border_radius=5)
        pygame.draw.rect(self.screen, BLACK, self.buttons['pid_tune'], 2, border_radius=5)
        label = self.button_font.render("TUNE PID", True, BLACK)
        self.screen.blit(label, label.get_rect(center=self.buttons['pid_tune'].center))

        pid_text = f"PID: Kp={self.pid.kp:.1f} Ki={self.pid.ki:.1f} Kd={self.pid.kd:.2f}"
        self.screen.blit(self.small_font.render(pid_text, True, DARK_GRAY), (40, 235))

    def draw_status_panel(self):
        panel_x = 780; panel_y = 30; panel_w = SCREEN_WIDTH - panel_x - 20; panel_h = 340
        pygame.draw.rect(self.screen, (240, 240, 240), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)
        self.screen.blit(self.title_font.render("SYSTEM STATUS", True, DARK_GRAY), (panel_x + 20, panel_y + 10))
        pygame.draw.line(self.screen, DARK_GRAY, (panel_x + 20, panel_y + 50), (panel_x + panel_w - 20, panel_y + 50), 2)
        col1_x = panel_x + 30; col2_x = panel_x + panel_w // 2 + 20

        status_texts_col1 = [ f"SYSTEM: {'ACTIVE' if self.system_active else 'INACTIVE'}", "", f"FEEDING: {'IN PROGRESS' if self.motor.is_feeding else 'IDLE'}", "", f"MOTOR ANGLE: {self.motor.current_angle:.1f}°", f"TARGET ANGLE: {self.motor.target_angle:.1f}°", f"MOTOR RPM: {self.motor.get_rpm():.1f}", ]
        status_texts_col2 = [ f"VOLTAGE: {self.motor.voltage:.2f}V", f"CURRENT: {self.motor.current:.3f}A", "", "", f"FEED LEVEL: {self.feed_level:.0f}%", f"SESSIONS: {self.feeding_system.feed_sessions}", f"TOTAL DISP.: {self.feeding_system.total_feed_dispensed*1000:.1f}ml",]

        start_y = panel_y + 65; line_height = 30
        for i, text in enumerate(status_texts_col1):
            color = DARK_GRAY
            if "SYSTEM:" in text: color = GREEN if self.system_active else RED
            elif "FEEDING:" in text: color = YELLOW if self.motor.is_feeding else GREEN
            self.screen.blit(self.font.render(text, True, color), (col1_x, start_y + i * line_height))
        for i, text in enumerate(status_texts_col2):
            self.screen.blit(self.font.render(text, True, DARK_GRAY), (col2_x, start_y + i * line_height))

    def draw_performance_graph(self):
        graph_x = 780; status_panel_h = 340; status_panel_y = 30
        graph_y = status_panel_y + status_panel_h + 20; graph_w = SCREEN_WIDTH - graph_x - 20; graph_h = SCREEN_HEIGHT - graph_y - 20
        graph_rect = pygame.Rect(graph_x, graph_y, graph_w, graph_h)
        pygame.draw.rect(self.screen, WHITE, graph_rect); pygame.draw.rect(self.screen, BLACK, graph_rect, 2)
        self.screen.blit(self.font.render("MOTOR ANGLE (PID TRACKING)", True, DARK_GRAY), (graph_rect.x + 10, graph_rect.y + 5))
        if len(self.angle_history) < 2: return
        for i in range(1, 4): pygame.draw.line(self.screen, (220, 220, 220), (graph_rect.x, graph_rect.y + i * (graph_rect.height // 4)), (graph_rect.right, graph_rect.y + i * (graph_rect.height // 4)))
        for i in range(1, 6): pygame.draw.line(self.screen, (220, 220, 220), (graph_rect.x + i * (graph_rect.width // 6), graph_rect.y), (graph_rect.x + i * (graph_rect.width // 6), graph_rect.bottom))
        all_vals = list(self.angle_history) + list(self.target_angle_history)
        if not all_vals: return
        min_val = min(all_vals); max_val = max(all_vals); val_range = max(max_val - min_val, 10)
        def get_points(history_data):
            points = []; num_p = len(history_data)
            if num_p <= 1: return [(graph_rect.x, graph_rect.centery)]
            for i, val in enumerate(history_data):
                x_coord = graph_rect.x + (i * graph_rect.width) // (num_p -1)
                y_coord = graph_rect.bottom - int(((val - min_val) / val_range) * graph_rect.height)
                y_coord = max(graph_rect.top, min(graph_rect.bottom -1, y_coord))
                points.append((x_coord, y_coord))
            return points
        if len(self.angle_history) > 1: pygame.draw.lines(self.screen, BLUE, False, get_points(self.angle_history), 2)
        if len(self.target_angle_history) > 1: pygame.draw.lines(self.screen, RED, False, get_points(self.target_angle_history), 2)
        legend_y_base = graph_rect.bottom + 5
        pygame.draw.line(self.screen, BLUE, (graph_rect.x + 10, legend_y_base + 5), (graph_rect.x + 30, legend_y_base + 5), 2)
        self.screen.blit(self.small_font.render("Current Angle", True, DARK_GRAY), (graph_rect.x + 35, legend_y_base))
        pygame.draw.line(self.screen, RED, (graph_rect.x + 150, legend_y_base + 5), (graph_rect.x + 170, legend_y_base + 5), 2)
        self.screen.blit(self.small_font.render("Target Angle", True, DARK_GRAY), (graph_rect.x + 175, legend_y_base))

    def draw_feed_particles(self):
        for particle in self.feeding_system.feed_particles:
            if particle['eaten']: continue
            alpha = max(0, min(255, int(particle['life'] * 1.7)))
            size = max(1, particle['size'])
            s = pygame.Surface((size*2, size*2), pygame.SRCALPHA)
            pygame.draw.circle(s, (*particle['color'], alpha), (size, size), size)
            self.screen.blit(s, (particle['x']-size, particle['y']-size))

    def draw_water_tank(self):
        pygame.draw.rect(self.screen, (180, 210, 240), self.tank_rect)
        pygame.draw.rect(self.screen, DARK_GRAY, self.tank_rect, 5, border_radius=5)
        gravel_rect = pygame.Rect(self.tank_rect.x + 3, self.tank_rect.bottom - 20, self.tank_rect.width - 6, 20)
        pygame.draw.rect(self.screen, GRAVEL_COLOR, gravel_rect)

        for plant in self.plants:
            pygame.draw.rect(self.screen, plant['color'], plant['rect'])
            for i in range(3):
                leaf_y = plant['rect'].y + (plant['rect'].height / 4) * (i + 1)
                leaf_w = plant['rect'].width * 1.5; leaf_h = 10
                side = 1 if i % 2 == 0 else -1
                leaf_x = plant['rect'].centerx if side == 1 else plant['rect'].centerx - leaf_w
                pygame.draw.ellipse(self.screen, plant['color'], (leaf_x, leaf_y, leaf_w, leaf_h))

        water_fill_rect = pygame.Rect(self.tank_rect.x + 3, self.water_surface_y + 3, self.tank_rect.width - 6, self.tank_rect.height - (self.water_surface_y - self.tank_rect.y) - 6)
        s_water = pygame.Surface((water_fill_rect.width, water_fill_rect.height), pygame.SRCALPHA)
        s_water.fill(WATER_BLUE)
        self.screen.blit(s_water, water_fill_rect.topleft)
        pygame.draw.line(self.screen, (60, 100, 200), (self.tank_rect.left + 3, self.water_surface_y), (self.tank_rect.right - 3, self.water_surface_y), 3)

        for fish in self.fish_list:
            w, h = fish['width'], fish['height']
            is_flipped = fish['facing_direction'] < 0
            fish_color = fish['color']
            outline_color = DARK_BROWN
            fish_surf = pygame.Surface((w + 20, h + 10), pygame.SRCALPHA)
            body_center_y = (h + 10) // 2
            body_start_x = 15
            body_end_x = body_start_x + w - 10
            body_points = [ (body_end_x, body_center_y), (body_end_x * 0.9 + body_start_x * 0.1, body_center_y - h * 0.5), (body_end_x * 0.3 + body_start_x * 0.7, body_center_y - h * 0.4), (body_start_x, body_center_y - 3), (body_start_x, body_center_y + 3), (body_end_x * 0.3 + body_start_x * 0.7, body_center_y + h * 0.4), (body_end_x * 0.9 + body_start_x * 0.1, body_center_y + h * 0.5), ]
            pygame.draw.polygon(fish_surf, fish_color, body_points)
            pygame.draw.polygon(fish_surf, outline_color, body_points, 1)
            tail_sway = math.sin(fish['tail_phase']) * 6
            tail_base_x = body_start_x
            tail_tip_x = tail_base_x - 12
            tail_points = [ (tail_base_x, body_center_y - 2), (tail_tip_x, body_center_y - h//2 + tail_sway), (tail_base_x - 4, body_center_y), (tail_tip_x, body_center_y + h//2 - tail_sway), (tail_base_x, body_center_y + 2), ]
            pygame.draw.polygon(fish_surf, fish_color, tail_points)
            pygame.draw.polygon(fish_surf, outline_color, tail_points, 1)
            dorsal_base = body_end_x * 0.6 + body_start_x * 0.4
            dorsal_points = [ (dorsal_base - 5, body_center_y - h * 0.45), (dorsal_base, body_center_y - h * 0.5 - 6), (dorsal_base + 5, body_center_y - h * 0.45), ]
            pygame.draw.polygon(fish_surf, fish_color, dorsal_points)
            pygame.draw.polygon(fish_surf, outline_color, dorsal_points, 1)
            eye_x = body_end_x - 6; eye_y = body_center_y - 3
            pygame.draw.circle(fish_surf, WHITE, (eye_x, eye_y), 4)
            pygame.draw.circle(fish_surf, BLACK, (eye_x, eye_y), 2)
            mouth_x = body_end_x + 1; mouth_y = body_center_y + 2
            if fish['state'] == 'eating' and (fish['eat_timer'] // 2) % 2 == 0: pygame.draw.circle(fish_surf, BLACK, (mouth_x, mouth_y), 2)
            else: pygame.draw.line(fish_surf, BLACK, (mouth_x - 2, mouth_y), (mouth_x, mouth_y), 1)
            final_fish_surf = pygame.transform.flip(fish_surf, True, False) if is_flipped else fish_surf
            blit_x = fish['x'] - (5 if is_flipped else 15); blit_y = fish['y'] - 5
            self.screen.blit(final_fish_surf, (blit_x, blit_y))

        for ripple in self.water_ripples:
            alpha = max(0, min(255, int(ripple['alpha'])))
            if alpha > 0:
                s_ripple = pygame.Surface((ripple['radius']*2, ripple['radius']*2), pygame.SRCALPHA)
                pygame.draw.circle(s_ripple, (150, 180, 255, alpha//2), (ripple['radius'], ripple['radius']), ripple['radius'], 1)
                self.screen.blit(s_ripple, (ripple['x']-ripple['radius'], ripple['y']-ripple['radius']))

    def draw(self):
        for y_pos in range(SCREEN_HEIGHT):
            r = int(255 - (y_pos / SCREEN_HEIGHT) * 60); g = int(250 - (y_pos / SCREEN_HEIGHT) * 55); b = int(245 - (y_pos / SCREEN_HEIGHT) * 50)
            pygame.draw.line(self.screen, (max(0,r), max(0,g), max(0,b)), (0, y_pos), (SCREEN_WIDTH, y_pos))

        self.draw_water_tank()
        self.draw_feed_particles()
        self.draw_motor_assembly()
        self.draw_control_panel()
        self.draw_status_panel()
        self.draw_performance_graph()
        pygame.display.flip()

    def run(self):
        while self.running:
            self.handle_events()
            self.update_system()
            self.draw()
            self.clock.tick(FPS)
        pygame.quit()

if __name__ == '__main__':
    simulator = FishFeederSimulator()
    simulator.run()