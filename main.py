import pygame
import cv2
import mediapipe as mp
import random
import time

# Initialize pygame
pygame.init()

# Set up the game screen
screen_width, screen_height = 800, 600
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption('Zombie Game')

# Load assets
zombie_image = pygame.image.load("assets/zombie.gif")
zombie_image = pygame.transform.scale(zombie_image, (100, 100))

# Load sound effects
shoot_sound = pygame.mixer.Sound("assets/shoot_sound.mp3")

# Load gun pointer image (crosshair or gun image)
gun_pointer_image = pygame.image.load("assets/gun_pointer.png")
gun_pointer_image = pygame.transform.scale(gun_pointer_image, (30, 30))  # Adjust size as necessary

# Placeholder for background image (later replace with actual image)
background_image = pygame.Surface((screen_width, screen_height))  # Temporary blank surface
background_image.fill((50, 50, 50))  # Gray background, replace with actual image later

# Mediapipe hand detection setup
mp_hands = mp.solutions.hands
hands = mp_hands.Hands()

# Game parameters
zombie_speed = 5
zombies = []  # List to store zombie positions
zombie_count = 0  # Counter to track how many zombies have reached the gun
shooting = False  # Track shooting state
bullets = []  # List to store bullets

# Gun initial position (center of the screen on the x-axis, at the bottom)
gun_x, gun_y = screen_width // 2, screen_height - 50

# Helper function to detect gestures
def is_closed_fist(hand_landmarks):
    index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
    thumb_tip = hand_landmarks.landmark[mp_hands.HandLandmark.THUMB_TIP]
    
    if abs(index_finger_tip.x - thumb_tip.x) < 0.05 and abs(index_finger_tip.y - thumb_tip.y) < 0.05:
        return True
    return False

def gesture_control(hand_landmarks):
    if hand_landmarks:
        if is_closed_fist(hand_landmarks):
            return "shoot"
        else:
            return "stop"
    return "stop"

# Bullet movement function
def move_bullets():
    global bullets
    for bullet in bullets[:]:
        bullet[1] -= 10  # Move the bullet upwards
        if bullet[1] < 0:
            bullets.remove(bullet)

# Check collision between bullet and zombie
def check_bullet_collision(bullet, zombie):
    bullet_rect = pygame.Rect(bullet[0] - 5, bullet[1] - 5, 10, 10)  # Bullet hitbox (circle)
    zombie_rect = pygame.Rect(zombie[0], zombie[1], 100, 100)  # Zombie hitbox (rectangle)
    
    # Check if bullet and zombie collide
    return bullet_rect.colliderect(zombie_rect)

# Main game loop
cap = cv2.VideoCapture(0)  # Use the default webcam
running = True
while running:
    # Capture frame from the camera
    ret, frame = cap.read()
    if not ret:
        break

    # Convert frame to RGB (for Mediapipe)
    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    results = hands.process(frame_rgb)

    # Detect gestures and update shooting state
    if results.multi_hand_landmarks:
        hand_landmarks = results.multi_hand_landmarks[0]  # Assume one hand for simplicity
        action = gesture_control(hand_landmarks)

        if action == "shoot":
            if not shooting:
                print("Shooting started!")
                shooting = True
                shoot_sound.play()  # Play the shooting sound
                # Add a bullet at the gun's position
                bullets.append([gun_x, gun_y - 30])  # Add bullet above the gun

        elif action == "stop":
            if shooting:
                print("Shooting stopped!")
                shooting = False
        
        # Track the index finger position for gun pointer
        index_finger_tip = hand_landmarks.landmark[mp_hands.HandLandmark.INDEX_FINGER_TIP]
        gun_x = int(index_finger_tip.x * frame.shape[1])  # Convert normalized x to pixel value
        gun_x = max(0, min(screen_width - 30, gun_x))  # Restrict gun's x position within screen width

    # Mirror the gun's x position (flip horizontally)
    gun_x = screen_width - gun_x  # Reverse the direction of the gun movement

    # Move zombies down the screen and check if they reach the gun
    if len(zombies) < 3 and zombie_count < 10:  # Limit zombies to 3
        # Add a new zombie to the list at a random x position
        zombie_x = random.randint(0, screen_width - 100)  # Corrected random function
        zombies.append([zombie_x, 0])  # Start at the top of the screen

    # Update zombie positions
    for zombie in zombies[:]:
        zombie[1] += zombie_speed
        if zombie[1] >= gun_y:  # If the zombie reaches the gun
            zombie_count += 1
            zombies.remove(zombie)

    # Move bullets and check for collisions
    move_bullets()
    
    for bullet in bullets[:]:
        for zombie in zombies[:]:
            if check_bullet_collision(bullet, zombie):  # Bullet hits zombie
                zombies.remove(zombie)  # Remove zombie
                bullets.remove(bullet)  # Remove bullet
                break  # Exit the loop once bullet hits a zombie

    # Check for game over condition
    if zombie_count >= 10:
        # Game Over - Display message
        screen.fill((255, 0, 0))  # Red background
        font = pygame.font.SysFont(None, 72)
        game_over_text = font.render("You Died", True, (255, 255, 255))
        screen.blit(game_over_text, (screen_width // 2 - game_over_text.get_width() // 2, screen_height // 2 - game_over_text.get_height() // 2))
        pygame.display.flip()
        time.sleep(3)  # Show game over message for 3 seconds
        running = False  # End the game

    # Fill the screen with background (Placeholder)
    screen.blit(background_image, (0, 0))

    # Draw the zombies on the screen
    for zombie in zombies:
        screen.blit(zombie_image, (zombie[0], zombie[1]))

    # Draw the bullets (red dots) on the screen
    for bullet in bullets:
        pygame.draw.circle(screen, (255, 0, 0), (bullet[0], bullet[1]), 5)  # Red dot for bullet

    # Draw the gun pointer on the screen
    screen.blit(gun_pointer_image, (gun_x - 15, gun_y - 15))  # Adjust position to center the pointer

    # Display zombie count and shooting state
    font = pygame.font.SysFont(None, 36)
    shooting_text = font.render(f"Shooting: {'On' if shooting else 'Off'}", True, (255, 255, 255))
    zombie_count_text = font.render(f"Zombies Reached: {zombie_count}/10", True, (255, 255, 255))
    screen.blit(shooting_text, (10, 10))
    screen.blit(zombie_count_text, (10, 50))

    pygame.display.flip()  # Update the screen

    # Handle quitting the game
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
    
    # Optional: Frame rate control
    pygame.time.wait(30)  # Control frame rate

# Release resources
cap.release()
pygame.quit()
