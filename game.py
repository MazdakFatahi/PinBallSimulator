import pygame
import PinBallGameEnvironment as env
import numpy as np
import time

# INIT
all_times = []
cnt_left = 0
cnt_right = 0
cnt_left_success_hit, cnt_right_success_hit =0, 0
total_cnt_left = 0
total_cnt_right = 0
total_cnt_left_success_hit, total_cnt_right_success_hit =0, 0
bottom_area_height = 250
upper_area_height = 150
camera_fov = (256, 256)
height=bottom_area_height+camera_fov[1]+upper_area_height
width=256
num_episodes = 5
max_ball_speed = 1_000
flipper_rotation_speed_frac = 1
game = env.GameEnvironment(bottom_area_height=bottom_area_height, 
                           height=bottom_area_height+camera_fov[1]+upper_area_height, 
                           width=256, 
                           show_fov = True, 
                           camera_height = camera_fov[0], 
                           ball_radius=12, 
                           bumpers_radius=[15, 12, 12], 
                           num_leds = 10, 
                           save_speed_log=False, 
                           num_episodes = num_episodes, 
                           max_ball_speed = max_ball_speed, 
                           flipper_rotation_speed_frac = flipper_rotation_speed_frac)

prev_keys = pygame.key.get_pressed()
t0_episod = time.time()
t0_begining = time.time()

# GAME LOOP
while(True):

    keys = pygame.key.get_pressed()
    if keys[pygame.K_LEFT]  and keys[pygame.K_RIGHT]:
        action = 3
    if (not keys[pygame.K_LEFT]) and keys[pygame.K_RIGHT]:
        action = 2
    if keys[pygame.K_LEFT] and (not keys[pygame.K_RIGHT]):
        action = 1
    if (not keys[pygame.K_LEFT]) and (not keys[pygame.K_RIGHT]):
        action = 0

    _, game_over, _, left_success_hit, right_success_hit  = game.play_step(action=action)

    cnt_left_success_hit+=int(left_success_hit)
    cnt_right_success_hit+=int(right_success_hit)

    left_edge  = keys[pygame.K_LEFT]  and not prev_keys[pygame.K_LEFT]
    right_edge = keys[pygame.K_RIGHT] and not prev_keys[pygame.K_RIGHT]

    if left_edge == True:
        cnt_left += 1
        print('Left Edge')
    if right_edge == True:
        cnt_right += 1
        print('Right Edge')
    prev_keys = keys


    # game.update_ui()
    if not game.RUNING:
        game_over = False
        # pass
        break


    if game_over == True:
        print(f'Left: {cnt_left_success_hit}/{cnt_left} Right: {cnt_right_success_hit}/{cnt_right}')
        #print(cnt_left, cnt_right, cnt_left_success_hit, cnt_right_success_hit)
        total_cnt_left += cnt_left
        total_cnt_right += cnt_right
        total_cnt_left_success_hit += cnt_left_success_hit
        total_cnt_right_success_hit += cnt_right_success_hit        

        
        cnt_left = 0
        cnt_right = 0
        cnt_left_success_hit, cnt_right_success_hit = 0, 0

        all_times.append(time.time()-t0_episod)
        t0_episod = time.time()

    if game.episode_cnt == game.N_EPISODES:
        print('============== Total =====================')
        print(f'Left: {total_cnt_left_success_hit}/{total_cnt_left}             Right: {total_cnt_right_success_hit}/{total_cnt_right}')
#        print(total_cnt_left, total_cnt_right, total_cnt_left_success_hit, total_cnt_right_success_hit)
        print(f'Total time: {time.time() - t0_begining }')
        np.save(f'{time.time()}.npy',{"timing":np.array(all_times), "total_cnt_left": total_cnt_left, "total_cnt_right": total_cnt_right, "total_cnt_left_success_hit": total_cnt_left_success_hit, "total_cnt_right_success_hit":total_cnt_right_success_hit})


