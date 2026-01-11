import pygame, os
import numpy as np
import random
import time
import random
# Initialize Pygame
pygame.init()
pygame.display.set_caption("Pinball Game")
# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
RED   = (255, 0, 0)
GRAY  = (100, 100, 100)


class GameEnvironment():
    def __init__(self, width = 700, height = 1000, show_fov = False, camera_height = 128, bottom_area_height = 150, ball_radius = 15, bumpers_radius=[25, 20, 20], num_leds = 0, save_speed_log = False, log_filename = 'game.log', num_episodes = 10, max_ball_speed = 400, flipper_rotation_speed_frac = 1): 


        # --- Constants and Configuration ---
        self.WIDTH, self.HEIGHT = width, height              # Total window size (500 for playground, 150 for UI)
        self.PLAYGROUND_HEIGHT = self.HEIGHT - bottom_area_height              # Play area height
        
        self.FLIPPERs_Y = self.PLAYGROUND_HEIGHT - self.PLAYGROUND_HEIGHT//5
        self.CAMERA_UPPER_BOUND  = self.FLIPPERs_Y - camera_height
        self.SHOW_FOV = show_fov
        self.BALL_RADIUS = ball_radius
        self.BALL_INIT_SPEED_VX = 5                   # Initial speed of the ball
        self.BALL_INIT_SPEED_VY = 5                   # Initial speed of the ball
        self.BALL_INIT_X = self.WIDTH//2                   # Initial speed of the ball
        self.BALL_INIT_Y = self.PLAYGROUND_HEIGHT //2                   # Initial speed of the ball
        self.BALL_GOT_STUCK = False
        self.BUMPERS_RADIUS = bumpers_radius
        self.INIT_SCORE = 0
        self.INIT_N_BALLS = 1
        self.N_EPISODES = num_episodes

        self.left_success_hit = False
        self.right_success_hit = False
        self.LEFT_FLIPPER_TOUCH_NUM = 0
        self.RIGHT_FLIPPER_TOUCH_NUM = 0
        self.LEFT_FLIPPER_SUCCESS_HIT_NUM = 0
        self.RIGHT_FLIPPER_SUCCESS_HIT_NUM = 0
        self.LEFT_FLIPPER_PRESS_NUM = 0
        self.RIGHT_FLIPPER_PRESS_NUM = 0
        self.ball_start_time = time.time()
        # self.N_LED = n_led

        self.SAVE_SPEED_LOG = save_speed_log
        self.log_filename = log_filename

        # Friction, restitution, and gravity
        self.FRICTION = 0.995                      # Continuous friction factor
        self.WALL_RESTITUTION = 0.98               # Energy loss factor for wall bounces
        self.GRAVITY = 0.1                         # Gravity (pixels per frame added to vertical velocity)


        # Font for display (if needed)
        self.font = pygame.font.Font(None, 36)

        # Window setup
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        
        self.GAME_FPS = 60
        self.clock = pygame.time.Clock()
        self.RUNING = True
        self.START_GAME = False

        self.bumpers = []
        self.num_leds = num_leds
        self.leds = []

        self.flipper_rotation_speed_frac = flipper_rotation_speed_frac

        # Maximum speed
        self.MAX_SPEED_PX_PER_FRAME = (max_ball_speed/self.GAME_FPS)#10
        self.MAX_SPEED_PX_PER_SEC = max_ball_speed

        self.ball_speed_val_px_per_sec = 0
        self.ball_speed_val_px_per_frame = 0

        # Flipper settings (for a realistic pinball layout)
        self.left_flipper_pivot = np.array([self.WIDTH//4 , self.PLAYGROUND_HEIGHT - self.PLAYGROUND_HEIGHT//5 ])
        self.right_flipper_pivot = np.array([3*(self.WIDTH//4) , self.PLAYGROUND_HEIGHT - self.PLAYGROUND_HEIGHT//5 ])
        self.FLIPPER_LENGTH = self.WIDTH//4 - (self.BALL_RADIUS *5//4) #85 + 35                  # Flipper length
        self.FLIPPER_WIDTH = self.HEIGHT//80                    # Flipper thickness
        # Idle and active angles (in degrees):
        # Idle: left flipper at -45° (like "\"), right flipper at 45° (like "/")
        # Active: left flipper rotates to 0° (horizontal), right flipper to 180° (horizontal)
        self.LEFT_IDLE_ANGLE = 45
        self.RIGHT_IDLE_ANGLE = 135
        self.LEFT_ACTIVE_ANGLE = 0
        self.RIGHT_ACTIVE_ANGLE = 180
        self.FLIPPER_BOOST = 55.5                   # Boost factor when flipper is active
        # New constant for smooth flipper rotation (degrees per second)
        self.FLIPPER_ROTATION_SPEED = 500  

        # Initialize current flipper angles and target angles
        self.left_flipper_angle = self.LEFT_IDLE_ANGLE
        self.right_flipper_angle = self.RIGHT_IDLE_ANGLE
        self.left_flipper_target = self.LEFT_IDLE_ANGLE
        self.right_flipper_target = self.RIGHT_IDLE_ANGLE

        # Define drain gap (using active positions)
        self.left_gap = self.left_flipper_pivot[0] #+ FLIPPER_LENGTH   # 150 + 85 = 235
        self.right_gap = self.right_flipper_pivot[0] #- FLIPPER_LENGTH  # 350 - 85 = 265

        self.current_time = 0
        self.dt = 1/self.GAME_FPS

        self.time_tick_cnt = 0

        self.single_episode_game_over = False
        self.score = self.INIT_SCORE
        self.n_reamined_balls = self.INIT_N_BALLS
        self.episode_cnt = 0
        self.reward = 0
        self.cumulative_reward = 0
        
        self.POS_REWARD = 10
        self.NEG_REWARD = -10
        # Button settings
        self.button_rect_reset = pygame.Rect(self.WIDTH - 120, self.HEIGHT-50, 110, 40)

        self.button_start = pygame.Rect(20, self.HEIGHT-90, 100, 35)

        self.button_rect_quit = pygame.Rect( 20, self.HEIGHT-50, 100, 40)

        self.button_rect_record = pygame.Rect(self.WIDTH - 120, self.HEIGHT-90, 110, 35)

        # self.START_RECORDING = False


        self._reset()



    # --- Class Helper Functions ---
    def _rotate_point(self, point, angle):
        """Rotate a 2D point by angle (in degrees)."""
        rad = np.radians(angle)
        x, y = point
        return (x * np.cos(rad) - y * np.sin(rad),
                x * np.sin(rad) + y * np.cos(rad))

    def _point_segment_distance(self, p, a, b):
        """
        Compute the distance from point p to line segment ab.
        Returns (distance, closest_point)
        """
        p = np.array(p, dtype=float)
        a = np.array(a, dtype=float)
        b = np.array(b, dtype=float)
        ab = b - a
        if np.dot(ab, ab) == 0:
            return np.linalg.norm(p - a), a
        t = np.dot(p - a, ab) / np.dot(ab, ab)
        t = max(0, min(1, t))
        closest = a + t * ab
        return np.linalg.norm(p - closest), closest

    def _reflect_vector(self, v, n):
        """Reflect vector v about normalized vector n."""
        return v - 2 * np.dot(v, n) * n

    def _draw_flipper(self, surface, pivot, angle, length, width, mirror=False):
        """
        Draws a nail-shaped flipper as a tapered polygon.
        The base polygon (relative to pivot) is defined as:
        [(0,0), (length*0.7, -width/2), (length, 0), (length*0.7, width/2)]
        If mirror is True, the flipper is flipped vertically.
        The polygon is rotated by 'angle' and translated by the pivot.
        Returns the list of world coordinates for the polygon.
        """
        if not mirror:
            points = [(0, 0),
                    (length * 0.7, -width/2),
                    (length, 0),
                    (length * 0.7, width/2)]
        else:
            points = [(0, 0),
                    (length * 0.7, width/2),
                    (length, 0),
                    (length * 0.7, -width/2)]
        rotated_points = []
        for pt in points:
            rx, ry = self._rotate_point(pt, angle)
            rotated_points.append((pivot[0] + rx, pivot[1] + ry))
        pygame.draw.polygon(surface, WHITE, rotated_points)
        pygame.draw.polygon(surface, RED, rotated_points, 2)
        pygame.draw.circle(surface, WHITE, (int(pivot[0]), int(pivot[1])), 10)
        return rotated_points

    def _update_leds(self):
        # --- Update LED States ---
        for led in self.leds:
            if self.current_time - led["last_toggle"] > led["blink_interval"]:
                led["state"] = not led["state"]
                led["last_toggle"] = self.current_time


    def _update_flippers(self):
        # Smoothly update left flipper angle toward its target
        if self.left_flipper_angle < self.left_flipper_target:
            self.left_flipper_angle += self.FLIPPER_ROTATION_SPEED * self.flipper_rotation_speed_frac#0.02
            if self.left_flipper_angle > self.left_flipper_target:
                self.left_flipper_angle = self.left_flipper_target
        elif self.left_flipper_angle > self.left_flipper_target:
            self.left_flipper_angle -= self.FLIPPER_ROTATION_SPEED * self.flipper_rotation_speed_frac#0.02
            if self.left_flipper_angle < self.left_flipper_target:
                self.left_flipper_angle = self.left_flipper_target

        # Smoothly update right flipper angle toward its target
        if self.right_flipper_angle < self.right_flipper_target:
            self.right_flipper_angle += self.FLIPPER_ROTATION_SPEED * self.flipper_rotation_speed_frac#0.02
            if self.right_flipper_angle > self.right_flipper_target:
                self.right_flipper_angle = self.right_flipper_target
        elif self.right_flipper_angle > self.right_flipper_target:
            self.right_flipper_angle -= self.FLIPPER_ROTATION_SPEED * self.flipper_rotation_speed_frac#0.02
            if self.right_flipper_angle < self.right_flipper_target:
                self.right_flipper_angle = self.right_flipper_target


    def _check_flippers_collision(self, action):
        self.left_success_hit = False
        self.right_success_hit = False
        if action == 1:
        # --- Flipper Collision Detection ---
        # Left flipper collision
        # left_tip = left_flipper_pivot + np.array(self._rotate_point((FLIPPER_LENGTH, 0), left_flipper_angle))
        # Extend hitbox length by 10% for collision detection
            collision_length = self.FLIPPER_LENGTH * 1.1  
            left_tip = self.left_flipper_pivot + np.array(self._rotate_point((collision_length, 0), self.left_flipper_angle))

            dist, closest = self._point_segment_distance((self.ball_x, self.ball_y), self.left_flipper_pivot, left_tip)
            if dist < self.BALL_RADIUS:
                
                collision_vec = np.array([self.ball_x, self.ball_y]) - closest
                if np.linalg.norm(collision_vec) != 0:
                    normal = collision_vec / np.linalg.norm(collision_vec)
                    v = np.array([self.ball_vx_px_per_frame, self.ball_vy_px_per_frame])
                    v_reflected = self._reflect_vector(v, normal)
                    self.left_hit = True
                    self.LEFT_FLIPPER_TOUCH_NUM += 1

                    if action == 1:
                        v_reflected *= self.FLIPPER_BOOST
                        self.left_success_hit = True
                        # self.right_success_hit = False
                        # self.right_hit = False
                        self.LEFT_FLIPPER_SUCCESS_HIT_NUM += 1

                        print("left_success_hit")
                    # else:
                    #     print("left_touch")
                    self.ball_vx_px_per_frame, self.ball_vy_px_per_frame = v_reflected
                    self.ball_x, self.ball_y = closest + normal * (self.BALL_RADIUS + 20)
        if action == 2:            
            # Right flipper collision
            # right_tip = right_flipper_pivot + np.array(self._rotate_point((FLIPPER_LENGTH, 0), right_flipper_angle))
            collision_length = self.FLIPPER_LENGTH * 1.1
            right_tip = self.right_flipper_pivot + np.array(self._rotate_point((collision_length, 0), self.right_flipper_angle))

            dist, closest = self._point_segment_distance((self.ball_x, self.ball_y), self.right_flipper_pivot, right_tip)
            if dist < self.BALL_RADIUS:
                
                collision_vec = np.array([self.ball_x, self.ball_y]) - closest
                if np.linalg.norm(collision_vec) != 0:
                    normal = collision_vec / np.linalg.norm(collision_vec)
                    v = np.array([self.ball_vx_px_per_frame, self.ball_vy_px_per_frame])
                    v_reflected = self._reflect_vector(v, normal)
                    # self.right_hit = True
                    self.RIGHT_FLIPPER_TOUCH_NUM += 1

                    if action == 2:
                        v_reflected *= self.FLIPPER_BOOST
                        # self.left_hit = False
                        # self.left_success_hit = False
                        self.right_success_hit = True
                        self.RIGHT_FLIPPER_SUCCESS_HIT_NUM += 1


                        print("right_success_hit")
                    # else:
                    #     print("right_touch")
                    self.ball_vx_px_per_frame, self.ball_vy_px_per_frame = v_reflected
                    self.ball_x, self.ball_y = closest + normal * (self.BALL_RADIUS + 20)

    def _check_bumpers_collision(self):

        # --- Bumper Collision Detection ---
        for bumper in self.bumpers:
            dx = self.ball_x - bumper["x"]
            dy = self.ball_y - bumper["y"]
            dist = np.sqrt(dx**2 + dy**2)
            if dist < self.BALL_RADIUS + bumper["radius"]:
                normal = np.array([dx, dy])
                if np.linalg.norm(normal) != 0:
                    normal = normal / np.linalg.norm(normal)
                v = np.array([self.ball_vx_px_per_frame, self.ball_vy_px_per_frame])
                v_reflected = self._reflect_vector(v, normal)
                self.ball_vx_px_per_frame, self.ball_vy_px_per_frame = v_reflected * bumper["bounce"]
                self.ball_x = bumper["x"] + normal[0]*(self.BALL_RADIUS + bumper["radius"] + 1)
                self.ball_y = bumper["y"] + normal[1]*(self.BALL_RADIUS + bumper["radius"] + 1)
                # self.score += 1
                self.reward += self.POS_REWARD


    # Main functions
    def update_ui(self):
        if self.RUNING == True:    
            self.dt = self.clock.tick(self.GAME_FPS) / 1000.0  # Frame time in seconds # GAME_SPEED
            self.current_time = pygame.time.get_ticks() / 1000.0 # to update the blinker LEDs
            # print(self.dt, self.current_time)
            self.time_tick_cnt+=1

            if self.num_leds > 0: 
                self._update_leds()

            # --- Drawing ---
            self.screen.fill(BLACK)


            # Draw Reset Button
            pygame.draw.rect(self.screen, RED, self.button_rect_reset)
            font = pygame.font.Font(None, 30)
            text = font.render("RESET", True, WHITE)
            self.screen.blit(text, (self.button_rect_reset.x + 25, self.button_rect_reset.y + 10))

            # Draw quit Button
            pygame.draw.rect(self.screen, RED, self.button_rect_quit)
            font = pygame.font.Font(None, 30)
            text = font.render("QUIT", True, WHITE)
            self.screen.blit(text, (self.button_rect_quit.x + 25, self.button_rect_quit.y + 10))

            # Draw record Button
            pygame.draw.rect(self.screen, RED, self.button_rect_record)
            font = pygame.font.Font(None, 30)
            text = font.render("REC", True, WHITE)
            self.screen.blit(text, (self.button_rect_record.x + 25, self.button_rect_record.y + 10))


            # Draw start Button
            pygame.draw.rect(self.screen, RED, self.button_start)
            font = pygame.font.Font(None, 30)
            text = font.render("START", True, WHITE)
            self.screen.blit(text, (self.button_start.x + 25, self.button_start.y + 10))
            


            if self.num_leds > 0: 
                # Draw blinking LEDs in the background
                for led in self.leds:
                    if led["state"]:
                        pygame.draw.circle(self.screen, led["color"], (led["x"], led["y"]), led["radius"])
            
            # Draw ball and flippers on top of the LED background
            pygame.draw.circle(self.screen, WHITE, (int(self.ball_x), int(self.ball_y)), self.BALL_RADIUS)
            self._draw_flipper(self.screen, self.left_flipper_pivot, self.left_flipper_angle, self.FLIPPER_LENGTH, self.FLIPPER_WIDTH, mirror=False)
            self._draw_flipper(self.screen, self.right_flipper_pivot, self.right_flipper_angle, self.FLIPPER_LENGTH, self.FLIPPER_WIDTH, mirror=True)
            
            # Draw bumpers
            for bumper in self.bumpers:
                pygame.draw.circle(self.screen, bumper["color"], (int(bumper["x"]), int(bumper["y"])), bumper["radius"])
                pygame.draw.circle(self.screen, RED, (int(bumper["x"]), int(bumper["y"])), bumper["radius"], 2)
            
            # Draw bottom boundary segments for visual reference:
            # pygame.draw.line(self.screen, GRAY, (0, self.PLAYGROUND_HEIGHT), (self.left_gap, self.PLAYGROUND_HEIGHT), 3)
            # pygame.draw.line(self.screen, GRAY, (self.right_gap, self.PLAYGROUND_HEIGHT), (self.WIDTH, self.PLAYGROUND_HEIGHT), 3)
            pygame.draw.line(self.screen, GRAY, (0, self.left_flipper_pivot[1]), (self.left_gap, self.left_flipper_pivot[1]), 3)
            pygame.draw.line(self.screen, GRAY, (self.right_gap, self.left_flipper_pivot[1]), (self.WIDTH, self.left_flipper_pivot[1]), 3)


            # Camera boudary
            if self.SHOW_FOV == True:
                pygame.draw.line(self.screen, WHITE, (0, self.CAMERA_UPPER_BOUND), (self.WIDTH, self.CAMERA_UPPER_BOUND), 3)
                pygame.draw.line(self.screen, WHITE, (0, self.FLIPPERs_Y), (self.WIDTH, self.FLIPPERs_Y), 3)
                pygame.draw.line(self.screen, WHITE, (0, self.CAMERA_UPPER_BOUND), (0, self.FLIPPERs_Y), 3)
                pygame.draw.line(self.screen, WHITE, (self.WIDTH, self.CAMERA_UPPER_BOUND), (self.WIDTH, self.FLIPPERs_Y), 3)
            
            
            
            # Display Score and Ball Speed
            self.ball_speed_val_px_per_frame = np.sqrt(self.ball_vx_px_per_frame**2 + self.ball_vy_px_per_frame**2)
            # self.score_text = font.render(f"Score: {self.score}, Total reward: {self.cumulative_reward}", True, WHITE)
            # self.speed_text = font.render(f"Speed: {round(self.ball_speed_val_px_per_frame*self.GAME_FPS, 2)} px/s", True, WHITE)
            self.n_balls_text = font.render(f"Balls: {'O ' *self.n_reamined_balls} ", True, WHITE)
            self.screen.blit(self.n_balls_text, (10, self.PLAYGROUND_HEIGHT + 60))
            # self.speed_x_y_text = font.render(f" ball_vy: {round(self.ball_vy_px_per_frame, 1)}, ball_vx: {round(self.ball_vx_px_per_frame, 1)}", True, WHITE)
            # self.screen.blit(self.score_text, (10, self.PLAYGROUND_HEIGHT + 10))
            # self.screen.blit(self.speed_text, (10, self.PLAYGROUND_HEIGHT + 60))
            # self.screen.blit(self.speed_x_y_text, (10, self.PLAYGROUND_HEIGHT + 70))
            self.speed_text = font.render(f"Time:\n {self.current_time} s", True, WHITE)
            # self.speed_x_y_text = font.render(f" ball_vy: {round(self.ball_vy_px_per_frame, 1)}, ball_vx: {round(self.ball_vx_px_per_frame, 1)}", True, WHITE)
            # self.screen.blit(self.score_text, (10, self.PLAYGROUND_HEIGHT + 10))
            self.screen.blit(self.speed_text, (10, self.PLAYGROUND_HEIGHT + 10))
            
            pygame.display.flip()    




    def _reset_ball(self):
        # global ball_x, ball_y, ball_vx, ball_vy
        self.ball_x = self.BALL_INIT_X
        self.ball_y = self.BALL_INIT_Y
        self.ball_vx_px_per_frame = random.randint(3, 10)#self.BALL_INIT_SPEED_VX
        self.ball_vy_px_per_frame = random.randint(3, 10)#self.BALL_INIT_SPEED_VY
    def _reset_leds(self):
        # --- Blinking LED Setup (Background Effects) ---
        num_leds = self.num_leds
        self.leds = []
        for _ in range(num_leds):
            led = {
                "x": random.randint(10, self.WIDTH - 10),
                "y": random.randint(10, self.PLAYGROUND_HEIGHT - 10),
                "radius": 5,
                "color": (random.randint(0,255), random.randint(0,255), random.randint(0,255)),
                "blink_interval": random.uniform(0.5, 1.5),
                "last_toggle": 0.0,
                "state": True
            }
            self.leds.append(led)
        
    def _reset_bumpers(self):
        # Bumper settings
        self.bumpers = [
            # {"x": self.WIDTH // 2, "y": self.WIDTH //5, "radius": self.BUMPERS_RADIUS[0], "bounce": 1.2, "color": (0, 0, 255)},       # Blue bumper in center
            # {"x": self.WIDTH // 4, "y": self.WIDTH //3, "radius": self.BUMPERS_RADIUS[1], "bounce": 1.2, "color": (255, 0, 255)},       # Magenta bumper left
            # {"x": 3 * self.WIDTH // 4, "y": self.WIDTH //3, "radius": self.BUMPERS_RADIUS[2], "bounce": 1.2, "color": (255, 255, 0)}    # Yellow bumper right
            {"x": self.WIDTH // 2, "y": self.HEIGHT //5, "radius": self.BUMPERS_RADIUS[0], "bounce": 1.2, "color": (0, 0, 255)},       # Blue bumper in center
            {"x": self.WIDTH // 4, "y": self.HEIGHT //3, "radius": self.BUMPERS_RADIUS[1], "bounce": 1.2, "color": (255, 0, 255)},       # Magenta bumper left
            {"x": 3 * self.WIDTH // 4, "y": self.HEIGHT //3, "radius": self.BUMPERS_RADIUS[2], "bounce": 1.2, "color": (255, 255, 0)}    # Yellow bumper right

        ]

    def _reset_flippers(self):
        # Initialize current flipper angles and target angles
        self.left_flipper_angle = self.LEFT_IDLE_ANGLE
        self.right_flipper_angle = self.RIGHT_IDLE_ANGLE
        self.left_flipper_target = self.LEFT_IDLE_ANGLE
        self.right_flipper_target = self.RIGHT_IDLE_ANGLE

    def _reset(self):
        # self.single_episode_game_over = False
        self.score = self.INIT_SCORE
        self.n_reamined_balls = self.INIT_N_BALLS
        self.reward = 0
        self.cumulative_reward = 0
        self._reset_ball()
        self._reset_bumpers()
        self.LEFT_FLIPPER_TOUCH_NUM = 0
        self.RIGHT_FLIPPER_TOUCH_NUM = 0
        self.LEFT_FLIPPER_SUCCESS_HIT_NUM = 0
        self.RIGHT_FLIPPER_SUCCESS_HIT_NUM = 0
        self.LEFT_FLIPPER_PRESS_NUM = 0
        self.RIGHT_FLIPPER_PRESS_NUM = 0
        self.left_success_hit = False
        self.right_success_hit = False

        if self.num_leds > 0: 
            self._reset_leds()

    # def _check_if_the_ball_got_stuck_at_the_bottom(self):
    #     # speed_val = math.hypot(self.ball_vx_px_per_frame, self.ball_vy_px_per_frame)    
    #     if (np.round(np.abs(self.ball_vx_px_per_frame), 1) == 0) and (np.round(np.abs(self.ball_vy_px_per_frame), 1) == 0) and (self.ball_y + self.BALL_RADIUS >= self.PLAYGROUND_HEIGHT):
    #         return True
    #     return False
    #         # self._reset_ball()  # reset ball if not game over
    #         # return self._get_state(), reward, done, {}

    def _check_if_the_ball_got_stuck_at_the_bottom(self):
        # speed_val = math.hypot(self.ball_vx_px_per_frame, self.ball_vy_px_per_frame)    
        if (np.round(np.abs(self.ball_vx_px_per_frame), 1) == 0) and (np.round(np.abs(self.ball_vy_px_per_frame), 1) == 0) and (self.ball_y + self.BALL_RADIUS >= self.right_flipper_pivot[1]):
            return True
        return False
            # self._reset_ball()  # reset ball if not game over
            # return self._get_state(), reward, done, {}



    def _check_game_control(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.single_episode_game_over = True
                pygame.display.quit()
                self.RUNING = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.button_rect_reset.collidepoint(event.pos):
                    self._reset()
                if self.button_rect_quit.collidepoint(event.pos):
                    pygame.display.quit()
                    self.RUNING = False
                if self.button_rect_record.collidepoint(event.pos):
                    self.SAVE_SPEED_LOG = True
                if self.button_start.collidepoint(event.pos):
                    self.START_GAME = True
        

    def _check_wall_collidepoint(self):
        # --- Wall Collisions (with restitution) ---
        if self.ball_x - self.BALL_RADIUS <= 0:
            self.ball_x = self.BALL_RADIUS
            self.ball_vx_px_per_frame = -self.ball_vx_px_per_frame * self.WALL_RESTITUTION
        if self.ball_x + self.BALL_RADIUS >= self.WIDTH:
            self.ball_x = self.WIDTH - self.BALL_RADIUS
            self.ball_vx_px_per_frame = -self.ball_vx_px_per_frame * self.WALL_RESTITUTION

    def _check_top_wall_collision(self):

        # Top wall collision: add threshold to avoid infinite bouncing
        if self.ball_y - self.BALL_RADIUS <= 0:
            self.ball_y = self.BALL_RADIUS
            if abs(self.ball_vy_px_per_frame) < 0.2:
                self.ball_vy_px_per_frame = 0.2  # Nudge downward if vertical speed is very low
            else:
                self.ball_vy_px_per_frame = -self.ball_vy_px_per_frame * self.WALL_RESTITUTION

    def _check_drain(self):
        # --- Bottom Boundary: include gaps behind flippers ---

        # if self.ball_y + self.BALL_RADIUS >= self.left_flipper_pivot[1]:
        #     if not ((self.left_gap ) <= self.ball_x <= (self.right_gap )):
        #         self.ball_y = self.left_flipper_pivot[1] - self.BALL_RADIUS
        #         self.ball_vy_px_per_frame = -self.ball_vy_px_per_frame * self.WALL_RESTITUTION



        if self.episode_cnt<self.N_EPISODES:
            if self.ball_y + self.BALL_RADIUS >= self.left_flipper_pivot[1]+self.FLIPPER_LENGTH:
                if (self.left_gap ) <= self.ball_x <= (self.right_gap ):
                    # print(self.score)
                    self.n_reamined_balls -= 1
                    if self.n_reamined_balls > 0:
                        
                        self.reward += self.NEG_REWARD # Penalty for game_over or passing through the drain
                        self._reset_ball()
                        print(f'Episode, Reamined balls: {self.episode_cnt} -> {self.n_reamined_balls}')
                    else:
                        print("Oops! Game Over!")
                        self.current_time = 0
                        
                        self.single_episode_game_over = True  # Game over
                        self.episode_cnt += 1
                        if self.episode_cnt<self.N_EPISODES:
                            self._reset()
                        else:
                            print("No episodes left!")
                            self.single_episode_game_over = True  # Game over
                            
                            # pygame.display.quit()

                
    def _check_game_over(self):
        if self.n_reamined_balls == 0:
            self.single_episode_game_over = True
        else:
            self.single_episode_game_over = False
        if self.episode_cnt>=self.N_EPISODES:
            self.RUNING = False

            

        # if self.ball_y + self.BALL_RADIUS >= self.PLAYGROUND_HEIGHT:
        #     if (self.left_gap ) <= self.ball_x <= (self.right_gap ):
        #         self.score -= 1
        #         print(f'Score: {self.score}')
        #         self.reward += self.NEG_REWARD # Penalty for game_over or passing through the drain
        #         # print(self.score)
        #         if self.score > 0:
        #             print("Oops!")
        #             self._reset_ball()
        #         else:
        #             self.current_time = 0
                    
        #             self.single_episode_game_over = True  # Game over
                

    def _check_bottom_collision(self):
        if self.ball_y + self.BALL_RADIUS >= self.left_flipper_pivot[1]:#self.PLAYGROUND_HEIGHT-self.FLIPPER_LENGTH:
            if not ((self.left_gap ) <= self.ball_x <= (self.right_gap )):
                self.ball_y = self.left_flipper_pivot[1] - self.BALL_RADIUS
                self.ball_vy_px_per_frame = -self.ball_vy_px_per_frame * self.WALL_RESTITUTION

    # def _check_bottom_collision(self):
    #     # --- Bottom Boundary: include gaps behind flippers ---

    #     # if self.ball_y + self.BALL_RADIUS >= self.left_flipper_pivot[1]:
    #     #     if not ((self.left_gap ) <= self.ball_x <= (self.right_gap )):
    #     #         self.ball_y = self.left_flipper_pivot[1] - self.BALL_RADIUS
    #     #         self.ball_vy_px_per_frame = -self.ball_vy_px_per_frame * self.WALL_RESTITUTION


    #     if self.ball_y + self.BALL_RADIUS >= self.PLAYGROUND_HEIGHT:
    #         if (self.left_gap ) <= self.ball_x <= (self.right_gap ):
    #             self.score -= 1
    #             self.reward += self.NEG_REWARD # Penalty for game_over or passing through the drain
    #             # print(self.score)
    #             if self.score > 0:
    #                 self._reset_ball()
    #             else:
    #                 self.current_time = 0
                    
    #                 self.single_episode_game_over = True  # Game over
                
    #         else:
    #             self.ball_y = self.PLAYGROUND_HEIGHT - self.BALL_RADIUS
    #             self.ball_vy_px_per_frame = -self.ball_vy_px_per_frame * self.WALL_RESTITUTION

    def play_step(self, action):
        """
        action: integer {0,1,2,3} as defined:
           0: do nothing
           1: activate left flipper only
           2: activate right flipper only
           3: activate both flippers
        """
        if self.RUNING == True:
            
            self.reward = 0

            self._check_game_control()
            # --- Flipper Controls (replace the discrete state code) ---

            # --- Set flipper target angles based on action ---
            if action == 1:
                self.left_flipper_target = self.LEFT_ACTIVE_ANGLE
                self.right_flipper_target = self.RIGHT_IDLE_ANGLE  
                self.LEFT_FLIPPER_PRESS_NUM += 1
            elif action == 2:
                self.left_flipper_target = self.LEFT_IDLE_ANGLE
                self.right_flipper_target = self.RIGHT_ACTIVE_ANGLE
                self.RIGHT_FLIPPER_PRESS_NUM += 1
            elif action == 3:
                self.left_flipper_target = self.LEFT_ACTIVE_ANGLE
                self.right_flipper_target = self.RIGHT_ACTIVE_ANGLE
                self.LEFT_FLIPPER_PRESS_NUM += 1
                self.RIGHT_FLIPPER_PRESS_NUM += 1

            else:
                self.left_flipper_target = self.LEFT_IDLE_ANGLE
                self.right_flipper_target = self.RIGHT_IDLE_ANGLE
                self.left_press = False            
                self.right_press = False



            self._update_flippers()

            
            # gravity and ball x y update, were here



            

            # print(self.ball_x, self.ball_vx_px_per_frame)
            # print(self.ball_y, self.ball_vy_px_per_frame)

            self._check_flippers_collision(action)
            self._check_wall_collidepoint()
            self._check_top_wall_collision()
            self._check_bumpers_collision()
            self._check_bottom_collision()
            if self.START_GAME == True:
                self._check_game_over()
                self._check_drain()

            self.update_ui()# update was after playstep in the pipeline_MV
            
            
            # --- Apply Gravity ---
            self.ball_vy_px_per_frame += self.GRAVITY

            # --- Update Ball Position ---
            self.ball_x += self.ball_vx_px_per_frame
            self.ball_y += self.ball_vy_px_per_frame
            
            
            if self._check_if_the_ball_got_stuck_at_the_bottom():
                self.BALL_GOT_STUCK = True
                self._reset_ball()
            else:
                self.BALL_GOT_STUCK = False
            
            # --- Apply Friction ---
            self.ball_vx_px_per_frame *= self.FRICTION
            self.ball_vy_px_per_frame *= self.FRICTION

            # --- Enforce Maximum Speed ---
            self.ball_speed_val_px_per_frame = np.sqrt(self.ball_vx_px_per_frame**2 + self.ball_vy_px_per_frame**2) 
            
            self.ball_speed_val_px_per_sec = self.ball_speed_val_px_per_frame * self.GAME_FPS

            # if self.ball_speed_val_px_per_sec > self.MAX_SPEED_PX_PER_SEC:
            #     factor = (self.MAX_SPEED_PX_PER_SEC / self.GAME_FPS) / self.ball_speed_val_px_per_frame
            #     self.ball_vx_px_per_frame *= factor
            #     self.ball_vy_px_per_frame *= factor

            if self.ball_speed_val_px_per_frame > self.MAX_SPEED_PX_PER_FRAME:
                factor = self.MAX_SPEED_PX_PER_FRAME / self.ball_speed_val_px_per_frame
                self.ball_vx_px_per_frame *= factor
                self.ball_vy_px_per_frame *= factor
            # self.current_time += self.dt
            self.cumulative_reward += self.reward # track an episode reward


            if self.SAVE_SPEED_LOG:
                print(self.ball_speed_val_px_per_frame*self.GAME_FPS, self.ball_vx_px_per_frame*self.GAME_FPS, self.ball_vy_px_per_frame*self.GAME_FPS)
                if not os.path.exists(self.log_filename):
                    with open(self.log_filename, 'a') as f:
                        f.write(f'time,ball_x,ball_y,vx,vy,v\n')
                    with open(self.log_filename, 'a') as f:
                        f.write(f'{self.time_tick_cnt},{self.ball_x},{self.ball_y},{self.ball_vx_px_per_frame* self.GAME_FPS},{self.ball_vy_px_per_frame* self.GAME_FPS},{self.ball_speed_val_px_per_frame* self.GAME_FPS}\n') #,{np.sqrt((self.ball_vx_px_per_frame)**2 + (self.ball_vy_px_per_frame)**2)}\n')                        
                else:
                    with open(self.log_filename, 'a') as f:
                        f.write(f'{self.time_tick_cnt},{self.ball_x},{self.ball_y},{self.ball_vx_px_per_frame* self.GAME_FPS},{self.ball_vy_px_per_frame* self.GAME_FPS},{self.ball_speed_val_px_per_frame* self.GAME_FPS}\n') #,{np.sqrt((self.ball_vx_px_per_frame)**2 + (self.ball_vy_px_per_frame)**2)}\n')                        


        # else:
        #     self.single_episode_game_over = True  # Game over
        
        return self.reward, self.single_episode_game_over, self.score, self.left_success_hit, self.right_success_hit 

        



        
