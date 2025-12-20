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
    def __init__(self, kp=2.0, ki=0.5, kd=0.1):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.prev_error = 0
        self.integral = 0
        self.max_integral = 25

    def calculate(self, setpoint, current_value, dt):
        error = setpoint - current_value
        self.integral += error * dt
        self.integral = max(-self.max_integral, min(self.max_integral, self.integral))

        if dt > 1e-6:
            derivative = (error - self.prev_error) / dt
        else:
            derivative = 0.0

        output = (self.kp * error +
                  self.ki * self.integral +
                  self.kd * derivative)

        self.prev_error = error
        return output

    def reset(self):
        self.prev_error = 0
        self.integral = 0

class DCMotor:
    def __init__(self):
        self.voltage = 0.0
        self.current_angle = 0.0
        self.target_angle = 0.0
        self.angular_velocity = 0.0

        self.max_voltage = 12.0
        self.max_angular_velocity = 720.0

        self.resistance = 2.0
        self.torque_constant = 0.07
        self.back_emf_constant = 0.07
        self.friction = 0.01
        self.inertia = 0.012

        self.current = 0.0
        self.is_feeding = False
        self.feed_complete = True
        self.volume_per_rotation = 0.001

    def update(self, voltage_in, dt):
        self.voltage = max(-self.max_voltage, min(self.max_voltage, voltage_in))
        angular_velocity_rad_s = math.radians(self.angular_velocity)
        back_emf_voltage = self.back_emf_constant * angular_velocity_rad_s
        effective_voltage = self.voltage - back_emf_voltage
        self.current = effective_voltage / self.resistance
        motor_torque_val = self.torque_constant * self.current
        friction_torque_val = self.friction * angular_velocity_rad_s
        net_torque_val = motor_torque_val - friction_torque_val

        if abs(self.inertia) < 1e-6:
            angular_acceleration_rad_s2 = 0
        else:
            angular_acceleration_rad_s2 = net_torque_val / self.inertia

        angular_velocity_rad_s += angular_acceleration_rad_s2 * dt
        self.angular_velocity = math.degrees(angular_velocity_rad_s)
        self.angular_velocity = max(-self.max_angular_velocity, min(self.max_angular_velocity, self.angular_velocity))
        self.current_angle += self.angular_velocity * dt

        if self.is_feeding:
            angle_error = abs(self.target_angle - self.current_angle)
            if angle_error < 0.5 and abs(self.angular_velocity) < 1.0:
                self.feed_complete = True
                self.is_feeding = False
                self.angular_velocity = 0

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
        return abs(self.angular_velocity / 6.0)


class FeedingSystem:
    def __init__(self):
        self.total_feed_dispensed = 0.0
        self.feed_sessions = 0
        self.current_feed_volume = 0.0
        self.feed_particles = []

    def dispense_feed(self, volume, motor_angle_degrees, motor_center_x, motor_center_y, outlet_radius):
        particle_count = max(1, int(volume * 7000))
        spawn_angle_rad = math.radians(motor_angle_degrees)
        outlet_tip_x = motor_center_x + outlet_radius * math.cos(spawn_angle_rad)
        outlet_tip_y = motor_center_y + outlet_radius * math.sin(spawn_angle_rad)

        for _ in range(min(particle_count, 15)):
            offset_x = np.random.randint(-4, 5)
            offset_y = np.random.randint(-4, 5)
            base_speed = 1.2
            particle_vx = base_speed * math.cos(spawn_angle_rad) + np.random.uniform(-0.2, 0.2)
            particle_vy = base_speed * math.sin(spawn_angle_rad) + np.random.uniform(-0.2, 0.2) + 0.4

            particle = {
                'x': outlet_tip_x + offset_x,
                'y': outlet_tip_y + offset_y,
                'vx': particle_vx, 'vy': particle_vy,
                'life': 180 + np.random.randint(-40, 40),
                'size': max(1, int(volume * 3500)),
                'color': (np.random.randint(130, 180), np.random.randint(80, 120), np.random.randint(0, 30)),
                'shape': 'circle', 'settled': False, 'eaten': False
            }
            self.feed_particles.append(particle)

    def update_particles(self, tank_rect, water_surface_y):
        tank_visual_bottom_for_particles = tank_rect.bottom - 20
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

                if particle['y'] >= tank_visual_bottom_for_particles - particle['size']:
                    particle['y'] = tank_visual_bottom_for_particles - particle['size']
                    particle['vy'] = 0; particle['vx'] = 0
                    particle['settled'] = True; particle['life'] = 2500

                particle['x'] = max(tank_rect.left + 5 + particle['size'], min(tank_rect.right - 5 - particle['size'], particle['x']))

            particle['life'] -= 1
            if particle['life'] <= 0:
                 try: self.feed_particles.remove(particle)
                 except ValueError: pass

class FishFeederSimulator:
    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Enhanced Fish Feeder Simulation V12")
        self.clock = pygame.time.Clock()
        self.motor = DCMotor()

        # *** DEFINISI pid_academic_settings DIPINDAHKAN KE ATAS SEBELUM PEMANGGILAN _apply_pid_academic_setting ***
        self.pid_academic_settings = [
            {'kp': 2.2, 'Ti': 0.6, 'Td': 0.3,  'name': "Balanced"},
            {'kp': 6.0, 'Ti': 2.0, 'Td': 0.02, 'name': "Underdamped"},
            {'kp': 0.6, 'Ti': 1.0, 'Td': 0.4,  'name': "Overdamped"},
        ]
        self.current_pid_setting_index = 0
        self._apply_pid_academic_setting() # Sekarang atribut sudah ada saat dipanggil

        self.feeding_system = FeedingSystem()
        self.running = True
        self.system_active = False
        self.angle_history = deque(maxlen=300)
        self.target_angle_history = deque(maxlen=300)
        self.rpm_history = deque(maxlen=300)
        self.buttons = {}
        self.font = pygame.font.Font(None, 24)
        self.title_font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 16)
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
        self.motor_center_x = 500
        self.motor_center_y = 350
        self.motor_outlet_effective_radius = 30 + 10

    def _apply_pid_academic_setting(self):
        """Menerapkan setelan PID dari format Kp, Ti, Td."""
        current_academic_params = self.pid_academic_settings[self.current_pid_setting_index]
        kp_val = current_academic_params['kp']
        # Konversi Ti ke Ki: Ki = Kp / Ti
        ki_val = kp_val / current_academic_params['Ti'] if current_academic_params['Ti'] > 1e-6 else 0
        # Konversi Td ke Kd: Kd = Kp * Td
        kd_val = kp_val * current_academic_params['Td']

        if hasattr(self, 'pid'):
            self.pid.kp = kp_val
            self.pid.ki = ki_val
            self.pid.kd = kd_val
        else:
            self.pid = PIDController(kp=kp_val, ki=ki_val, kd=kd_val)
        self.pid.reset()


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
        padding = 10; fish_width_param = 35; fish_height_param = 20
        self.fish_visual_width = fish_width_param + 25
        self.fish_visual_height = fish_height_param + 15
        spawnable_width = self.tank_rect.width - self.fish_visual_width - padding * 2
        spawnable_height = (self.tank_rect.height - (self.water_surface_y - self.tank_rect.y)) - self.fish_visual_height - padding * 2
        if spawnable_width <= 0: spawnable_width = 1
        if spawnable_height <= 0: spawnable_height = 1
        brown_shades = [
            (139, 69, 19), (160, 82, 45), (128, 0, 0),
            (165, 42, 42), (101, 67, 33), (210, 105, 30),
            (193, 154, 107), (205, 133, 63), (244, 164, 96),
            (222, 184, 135), (188, 143, 143)
        ]
        for i in range(self.num_fish):
            initial_vx = np.random.uniform(0.5, 1.2) * np.random.choice([-1, 1])
            base_color = random.choice(brown_shades)
            r_offset, g_offset, b_offset = [np.random.randint(-15, 16) for _ in range(3)]
            fish_color = (max(0,min(255,base_color[0]+r_offset)),max(0,min(255,base_color[1]+g_offset)),max(0,min(255,base_color[2]+b_offset)))
            fin_r=max(0,min(255,fish_color[0]-np.random.randint(20,41))); fin_g=max(0,min(255,fish_color[1]-np.random.randint(20,41))); fin_b=max(0,min(255,fish_color[2]-np.random.randint(20,41)))
            fin_color = (fin_r, fin_g, fin_b)
            self.fish_list.append({
                'id': i, 'x': self.tank_rect.x+padding+np.random.randint(spawnable_width), 'y': self.water_surface_y+padding+np.random.randint(spawnable_height),
                'width': fish_width_param, 'height': fish_height_param, 'vx': initial_vx, 'vy': 0, 'color': fish_color, 'fin_color': fin_color,
                'target_particle': None, 'state': 'swimming', 'eat_timer': 0, 'tail_phase': np.random.uniform(0,2*math.pi),
                'facing_direction': 1 if initial_vx >=0 else -1, 'bob_offset': np.random.uniform(0,2*math.pi),
                'mouth_open_anim': False, 'mouth_anim_timer': random.randint(10,60) })

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT: self.running = False
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
            self.pid.reset()
            rotations = self.motor.start_feeding(volume)
            if rotations > 0:
                self.feeding_system.current_feed_volume = volume
                self.feeding_system.feed_sessions += 1
                self.feed_level = max(0, self.feed_level - volume * 1000)

    def emergency_stop(self):
        self.motor.is_feeding = False; self.motor.feed_complete = True
        self.motor.target_angle = self.motor.current_angle
        self.motor.angular_velocity = 0; self.motor.voltage = 0
        self.pid.reset()

    def reset_system(self):
        self.motor = DCMotor()
        self.current_pid_setting_index = 0
        self._apply_pid_academic_setting()
        self.feeding_system = FeedingSystem()
        self.system_active = False; self.feed_level = 100
        self.water_ripples = []
        self.angle_history.clear(); self.target_angle_history.clear(); self.rpm_history.clear()
        self._initialize_fish()

    def tune_pid(self):
        self.current_pid_setting_index = (self.current_pid_setting_index + 1) % len(self.pid_academic_settings)
        self._apply_pid_academic_setting()
        new_settings = self.pid_academic_settings[self.current_pid_setting_index]
        print(f"PID Tuned to: {new_settings['name']} -> Kp={self.pid.kp:.2f}, Ki={self.pid.ki:.2f} (from Ti={new_settings['Ti']}), Kd={self.pid.kd:.3f} (from Td={new_settings['Td']})")


    def _update_fish_behavior(self):
        search_radius_sq=250**2; chase_speed_x=1.8; chase_speed_y=1.5; eat_distance_sq=12**2
        available_particles = [p for p in self.feeding_system.feed_particles if not p['eaten'] and p['y'] > self.water_surface_y + 5]
        current_time_sim = time.time()
        for fish in self.fish_list:
            fish_center_x=fish['x'] + self.fish_visual_width/2
            fish_center_y=fish['y'] + self.fish_visual_height/2
            fish['tail_phase']=(fish['tail_phase'] + 0.7 * abs(fish['vx']/chase_speed_x + 0.1)) % (2*math.pi)
            original_vy = 0
            if fish['eat_timer'] > 0:
                fish['eat_timer']-=1
                if fish['eat_timer']==0: fish['state']='swimming'
                fish['mouth_open_anim'] = True
                continue
            if fish['target_particle'] and (fish['target_particle']['eaten'] or fish['target_particle'] not in self.feeding_system.feed_particles):
                 fish['target_particle']=None; fish['state']='swimming'
            if not fish['target_particle']:
                closest_particle_found=None; min_dist_sq_found=search_radius_sq
                for p in available_particles:
                    is_targeted=any(other_fish['target_particle']==p for other_fish in self.fish_list)
                    if is_targeted: continue
                    particle_center_x = p['x']; particle_center_y = p['y']
                    dx=particle_center_x-fish_center_x; dy=particle_center_y-fish_center_y
                    dist_sq=dx*dx+dy*dy
                    if dist_sq < min_dist_sq_found:
                        min_dist_sq_found=dist_sq; closest_particle_found=p
                if closest_particle_found:
                    fish['target_particle']=closest_particle_found; fish['state']='chasing'
                else: fish['state']='swimming'
            if fish['state']=='chasing' and fish['target_particle']:
                target=fish['target_particle']; dx=target['x']-fish_center_x; dy=target['y']-fish_center_y
                dist_sq=dx*dx+dy*dy
                fish['mouth_open_anim'] = True
                if dist_sq < eat_distance_sq:
                    target['eaten']=True; fish['state']='eating'; fish['eat_timer']=10
                    fish['target_particle']=None; fish['vx']=0; fish['vy']=0
                    for f in self.fish_list:
                        if f['target_particle']==target: f['target_particle']=None; f['state']='swimming'
                else:
                    dist=math.sqrt(dist_sq) if dist_sq > 0 else 1
                    fish['vx']=(dx/dist)*chase_speed_x; fish['vy']=(dy/dist)*chase_speed_y
            elif fish['state']=='swimming':
                original_vy = math.sin(current_time_sim * 2.5 + fish['bob_offset']) * 0.6
                if abs(fish['vx']) < 0.3: fish['vx']=np.random.uniform(0.5,1.2)*np.random.choice([-1,1])
                if np.random.random() < 0.01: fish['vx']*=-1
                fish['vy'] = original_vy
                fish['mouth_anim_timer'] -= 1
                if fish['mouth_anim_timer'] <= 0:
                    fish['mouth_open_anim'] = not fish['mouth_open_anim']
                    fish['mouth_anim_timer'] = random.randint(20, 40)
            else: fish['mouth_open_anim'] = False
            if abs(fish['vx']) > 0.1: fish['facing_direction']=1 if fish['vx'] > 0 else -1
            fish['x']+=fish['vx']; fish['y']+=fish['vy']

            if fish['x'] < self.tank_rect.left + 5:
                fish['x'] = self.tank_rect.left + 5; fish['vx'] *= -1
                if abs(fish['vx']) > 0.1: fish['facing_direction'] = 1
                fish['state'] = 'swimming'; fish['target_particle'] = None
            elif fish['x'] + self.fish_visual_width > self.tank_rect.right - 5:
                fish['x'] = self.tank_rect.right - 5 - self.fish_visual_width; fish['vx'] *= -1
                if abs(fish['vx']) > 0.1: fish['facing_direction'] = -1
                fish['state'] = 'swimming'; fish['target_particle'] = None
            max_y_fish = self.tank_rect.bottom - 20 - self.fish_visual_height + 5
            fish['y'] = max(self.water_surface_y + 5, min(max_y_fish, fish['y']))

    def update_system(self):
        current_time = time.time(); dt = current_time - self.last_time; self.last_time = current_time
        if dt <= 0: dt = 1/FPS
        if dt > 0.1: dt = 0.1

        if self.system_active:
            if self.motor.is_feeding:
                control_signal = self.pid.calculate(self.motor.target_angle, self.motor.current_angle, dt)
                voltage = max(-self.motor.max_voltage, min(self.motor.max_voltage, control_signal))
            else:
                voltage = 0
                if abs(self.motor.angular_velocity) > 0.1: voltage = -self.motor.angular_velocity * 0.1
                else: self.motor.angular_velocity = 0
        else:
            voltage = 0; self.motor.angular_velocity *= 0.90
            if abs(self.motor.angular_velocity) < 0.1: self.motor.angular_velocity = 0

        self.motor.update(voltage, dt); self.motor_shaft_angle = self.motor.current_angle

        if self.motor.is_feeding and abs(self.motor.angular_velocity) > 5:
            current_feed_rate = abs(self.motor.angular_velocity) / 360.0 * self.motor.volume_per_rotation
            if current_feed_rate > 0.00001:
                self.feeding_system.dispense_feed(
                    current_feed_rate * dt * FPS * 0.7,
                    self.motor.current_angle, self.motor_center_x, self.motor_center_y,
                    self.motor_outlet_effective_radius )
                if np.random.random() < 0.2:
                    ripple_x = self.motor_center_x + (self.motor_outlet_effective_radius + 5) * math.cos(math.radians(self.motor.current_angle))
                    ripple_y = self.motor_center_y + (self.motor_outlet_effective_radius + 5) * math.sin(math.radians(self.motor.current_angle))
                    if ripple_y < self.water_surface_y + 10 :
                         self.water_ripples.append({'x': ripple_x, 'y': self.water_surface_y + np.random.randint(0, 5), 'radius': 3, 'alpha': 255 })

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
        if self.system_active or len(self.angle_history) > 0 or self.motor.is_feeding :
            self.angle_history.append(self.motor.current_angle)
            self.target_angle_history.append(self.motor.target_angle)
            self.rpm_history.append(self.motor.get_rpm())
        elif len(self.angle_history) > 0 :
             if not self.motor.is_feeding and abs(self.motor.angular_velocity) < 0.1:
                 try:
                    self.angle_history.popleft(); self.target_angle_history.popleft(); self.rpm_history.popleft()
                 except IndexError: pass

    def draw_motor_assembly(self):
        center_x = self.motor_center_x; center_y = self.motor_center_y
        shaft_angle_rad = math.radians(self.motor_shaft_angle)
        pygame.draw.ellipse(self.screen, METAL_GRAY, (center_x - 60, center_y - 40, 120, 80))
        pygame.draw.ellipse(self.screen, DARK_METAL, (center_x - 60, center_y - 40, 120, 80), 3)
        pygame.draw.rect(self.screen, DARK_METAL, (center_x - 70, center_y - 10, 140, 20))
        pygame.draw.circle(self.screen, METAL_GRAY, (center_x, center_y), 30)
        pygame.draw.circle(self.screen, DARK_METAL, (center_x, center_y), 30, 3)
        shaft_marker_length = 28
        shaft_end_x = center_x + shaft_marker_length * math.cos(shaft_angle_rad)
        shaft_end_y = center_y + shaft_marker_length * math.sin(shaft_angle_rad)
        pygame.draw.line(self.screen, YELLOW, (center_x, center_y), (shaft_end_x, shaft_end_y), 5)
        num_other_blades = 2; blade_length = 22
        for i in range(1, num_other_blades + 1):
            blade_angle = shaft_angle_rad + i * (2 * math.pi / (num_other_blades + 1))
            blade_start_x = center_x + 5 * math.cos(blade_angle); blade_start_y = center_y + 5 * math.sin(blade_angle)
            blade_end_x = center_x + blade_length * math.cos(blade_angle); blade_end_y = center_y + blade_length * math.sin(blade_angle)
            pygame.draw.line(self.screen, ORANGE, (blade_start_x, blade_start_y), (blade_end_x, blade_end_y), 3)
        outlet_width_half = 10; outlet_length = 20; outlet_base_radius = 30
        angle_offset_rad = math.atan2(outlet_width_half, outlet_base_radius)
        p1_angle = shaft_angle_rad - angle_offset_rad; p2_angle = shaft_angle_rad + angle_offset_rad
        p1 = (center_x + outlet_base_radius*math.cos(p1_angle), center_y + outlet_base_radius*math.sin(p1_angle))
        p2 = (center_x + outlet_base_radius*math.cos(p2_angle), center_y + outlet_base_radius*math.sin(p2_angle))
        center_tip_x = center_x + (outlet_base_radius+outlet_length)*math.cos(shaft_angle_rad)
        center_tip_y = center_y + (outlet_base_radius+outlet_length)*math.sin(shaft_angle_rad)
        perp_dx_tip = -math.sin(shaft_angle_rad)*(outlet_width_half*0.8); perp_dy_tip = math.cos(shaft_angle_rad)*(outlet_width_half*0.8)
        p3 = (center_tip_x+perp_dx_tip, center_tip_y+perp_dy_tip); p4 = (center_tip_x-perp_dx_tip, center_tip_y-perp_dy_tip)
        outlet_points = [p1,p2,p3,p4]; pygame.draw.polygon(self.screen,METAL_GRAY,outlet_points); pygame.draw.polygon(self.screen,DARK_METAL,outlet_points,2)
        hole_radius_on_outlet = 4
        hole_center_x = center_x + (outlet_base_radius + outlet_length - hole_radius_on_outlet - 3) * math.cos(shaft_angle_rad)
        hole_center_y = center_y + (outlet_base_radius + outlet_length - hole_radius_on_outlet - 3) * math.sin(shaft_angle_rad)
        pygame.draw.circle(self.screen, (40,40,40), (hole_center_x, hole_center_y), hole_radius_on_outlet)

        indicator_feed_x = center_x - 70; indicator_feed_y = center_y - 55
        if self.motor.is_feeding:
            pygame.draw.circle(self.screen, YELLOW, (indicator_feed_x, indicator_feed_y), 8)
            feed_text_surface = self.small_font.render("FEED", True, BLACK)
            self.screen.blit(feed_text_surface, (indicator_feed_x - feed_text_surface.get_width() - 5, indicator_feed_y - feed_text_surface.get_height()//2))
            unit_label_text_surface = self.font.render("FEEDER UNIT", True, DARK_GRAY)
            self.screen.blit(unit_label_text_surface, (indicator_feed_x + 12, indicator_feed_y - unit_label_text_surface.get_height()//2))
        pygame.draw.circle(self.screen, BLACK, (indicator_feed_x, indicator_feed_y), 8, 1)

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

        current_academic_params = self.pid_academic_settings[self.current_pid_setting_index]
        pid_text_display = f"PID ({current_academic_params['name']}): Kp={self.pid.kp:.1f} Ti={current_academic_params['Ti']:.2f} Td={current_academic_params['Td']:.3f}"
        self.screen.blit(self.small_font.render(pid_text_display, True, DARK_GRAY), (self.buttons['power'].right + 15, 75))


    def draw_status_panel(self):
        panel_x = 780; panel_y = 30; panel_w = SCREEN_WIDTH - panel_x - 20; panel_h = 340
        pygame.draw.rect(self.screen, (240, 240, 240), (panel_x, panel_y, panel_w, panel_h), border_radius=10)
        pygame.draw.rect(self.screen, DARK_GRAY, (panel_x, panel_y, panel_w, panel_h), 3, border_radius=10)
        self.screen.blit(self.title_font.render("SYSTEM STATUS", True, DARK_GRAY), (panel_x + 20, panel_y + 10))
        pygame.draw.line(self.screen, DARK_GRAY, (panel_x + 20, panel_y + 50), (panel_x + panel_w - 20, panel_y + 50), 2)
        col1_x = panel_x + 30; col2_x = panel_x + panel_w // 2 + 20
        status_texts_col1 = [ f"SYSTEM: {'ACTIVE' if self.system_active else 'INACTIVE'}", "", f"PEMBERIAN PAKAN: {'PROSES' if self.motor.is_feeding else 'IDLE'}", "", f"SUDUT MOTOR : {self.motor.current_angle:.1f}°", f"TARGET SUDUT: {self.motor.target_angle:.1f}°", f"MOTOR RPM: {self.motor.get_rpm():.1f}", ]
        status_texts_col2 = [ f"TEGANGAN: {self.motor.voltage:.2f}V", f"ARUS: {self.motor.current:.3f}A", "", "", f"SISA PAKAN: {self.feed_level:.0f}%", f"SESSIONS: {self.feeding_system.feed_sessions}", f"TOTAL DISP.: {self.feeding_system.total_feed_dispensed*1000:.1f}ml",]
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
                leaf_w_original = plant['rect'].width * 1.5
                leaf_h = 10
                side = 1 if i % 2 == 0 else -1
                if side == 1: leaf_x_original = plant['rect'].centerx
                else: leaf_x_original = plant['rect'].centerx - leaf_w_original
                draw_leaf_x = leaf_x_original; draw_leaf_w = leaf_w_original
                tank_render_left_boundary = self.tank_rect.left + 5
                tank_render_right_boundary = self.tank_rect.right - 5
                if draw_leaf_x < tank_render_left_boundary:
                    overflow_left = tank_render_left_boundary - draw_leaf_x
                    draw_leaf_x = tank_render_left_boundary
                    draw_leaf_w = max(0, draw_leaf_w - overflow_left)
                if draw_leaf_x + draw_leaf_w > tank_render_right_boundary:
                    overflow_right = (draw_leaf_x + draw_leaf_w) - tank_render_right_boundary
                    draw_leaf_w = max(0, draw_leaf_w - overflow_right)
                if draw_leaf_w > 0:
                    pygame.draw.ellipse(self.screen, plant['color'], (draw_leaf_x, leaf_y, draw_leaf_w, leaf_h))

        water_fill_rect = pygame.Rect(self.tank_rect.x + 3, self.water_surface_y + 3, self.tank_rect.width - 6, self.tank_rect.height - (self.water_surface_y - self.tank_rect.y) - 6)
        s_water = pygame.Surface((water_fill_rect.width, water_fill_rect.height), pygame.SRCALPHA)
        s_water.fill(WATER_BLUE)
        self.screen.blit(s_water, water_fill_rect.topleft)
        pygame.draw.line(self.screen, (60, 100, 200), (self.tank_rect.left + 3, self.water_surface_y), (self.tank_rect.right - 3, self.water_surface_y), 3)

        for fish in self.fish_list:
            w, h = fish['width'], fish['height']
            is_flipped = fish['facing_direction'] < 0
            fish_surf_width = self.fish_visual_width
            fish_surf_height = self.fish_visual_height
            fish_surf = pygame.Surface((fish_surf_width, fish_surf_height), pygame.SRCALPHA)
            draw_offset_x = 10
            draw_offset_y = 5
            body_color = fish['color']
            fin_color = fish['fin_color']
            outline_color = (max(0, body_color[0]-50), max(0, body_color[1]-50), max(0, body_color[2]-50))
            mouth_color = (101, 67, 33)

            body_ellipse_rect = pygame.Rect(draw_offset_x + (w * 0.15), draw_offset_y, w * 0.7, h)
            pygame.draw.ellipse(fish_surf, body_color, body_ellipse_rect)

            num_lines = 2
            line_color_body = (max(0, body_color[0]-40), max(0, body_color[1]-40), max(0, body_color[2]-40), 150)
            for i in range(num_lines):
                line_y_pos = draw_offset_y + h * (0.35 + i * 0.3)
                start_x_line = body_ellipse_rect.left + body_ellipse_rect.width * 0.2
                end_x_line = body_ellipse_rect.right - body_ellipse_rect.width * 0.2
                pygame.draw.line(fish_surf, line_color_body, (start_x_line, line_y_pos) , (end_x_line, line_y_pos), 1)

            pygame.draw.ellipse(fish_surf, outline_color, body_ellipse_rect, 1)

            tail_sway = math.sin(fish['tail_phase']) * (h * 0.3)
            tail_base_x = draw_offset_x + (w * 0.15)
            tail_base_y = draw_offset_y + h // 2
            tail_length = w * 0.4
            tail_spread = h * 0.5
            tail_points = [
                (tail_base_x, tail_base_y),
                (tail_base_x - tail_length, tail_base_y - tail_spread + tail_sway),
                (tail_base_x - tail_length * 0.6, tail_base_y),
                (tail_base_x - tail_length, tail_base_y + tail_spread + tail_sway),
            ]
            pygame.draw.polygon(fish_surf, fin_color, tail_points)
            pygame.draw.polygon(fish_surf, outline_color, tail_points, 1)

            dorsal_base_start_x = draw_offset_x + w * 0.4
            dorsal_base_end_x = draw_offset_x + w * 0.7
            dorsal_tip_x = draw_offset_x + w * 0.55
            dorsal_tip_y = draw_offset_y - 5
            dorsal_points = [ (dorsal_base_start_x, draw_offset_y), (dorsal_tip_x, dorsal_tip_y), (dorsal_base_end_x, draw_offset_y) ]
            pygame.draw.polygon(fish_surf, fin_color, dorsal_points)
            pygame.draw.polygon(fish_surf, outline_color, dorsal_points, 1)

            ventral_base_start_x = draw_offset_x + w * 0.45
            ventral_base_end_x = draw_offset_x + w * 0.6
            ventral_tip_x = draw_offset_x + w * 0.5
            ventral_tip_y = draw_offset_y + h + 3
            ventral_points = [ (ventral_base_start_x, draw_offset_y + h), (ventral_tip_x, ventral_tip_y), (ventral_base_end_x, draw_offset_y + h) ]
            pygame.draw.polygon(fish_surf, fin_color, ventral_points)
            pygame.draw.polygon(fish_surf, outline_color, ventral_points, 1)

            eye_radius = max(3, h // 7)
            eye_x = draw_offset_x + w * 0.75
            eye_y = draw_offset_y + h * 0.35
            pygame.draw.circle(fish_surf, WHITE, (eye_x, eye_y), eye_radius)
            pygame.draw.circle(fish_surf, BLACK, (eye_x, eye_y), eye_radius // 2)
            pygame.draw.circle(fish_surf, WHITE, (eye_x + eye_radius // 3, eye_y - eye_radius // 3), eye_radius // 4)

            mouth_front_x = draw_offset_x + w * 0.88
            mouth_base_y = draw_offset_y + h * 0.6

            if fish['mouth_open_anim']:
                mouth_top_y = mouth_base_y - 2
                mouth_bottom_y = mouth_base_y + 2
                pygame.draw.line(fish_surf, mouth_color, (mouth_front_x - 3, mouth_base_y), (mouth_front_x, mouth_top_y), 1)
                pygame.draw.line(fish_surf, mouth_color, (mouth_front_x - 3, mouth_base_y), (mouth_front_x, mouth_bottom_y), 1)
            else:
                pygame.draw.line(fish_surf, mouth_color, (mouth_front_x - 3, mouth_base_y), (mouth_front_x, mouth_base_y), 1)

            final_fish_surf = pygame.transform.flip(fish_surf, True, False) if is_flipped else fish_surf
            self.screen.blit(final_fish_surf, (fish['x'], fish['y']))


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