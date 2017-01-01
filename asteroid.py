global end, canvas, graphics, scenes, scene, threads, canvas_cfg, score, settings, thread_refs, all_backing, old
import tkinter as tk
import threading, time, random

thread_refs = []

root = tk.Tk()
root.title('Asteroid')
class canvas_cfg:
    height = 400
    width = 550
canvas = tk.Canvas(root, bg='brown', height=canvas_cfg.height, width=canvas_cfg.width)
canvas.pack()

score = 0
class settings:
    class asteroids:
        use_multithreading = True
        difficulty_increment = 3 #Bigger number means that the game takes longer to progress
        fps_smoothing = 20 #Data cap - bigger number means more smoothing
        clip = True
    class laser:
        flash = 0.05
        times = 3
        colour = 'red'
    immunity = 3.2 #Immunity time (seconds)

class scripts:
    class start:
        def __init__(self):
            pass
        def background():
            global all_backing
            all_backing = []
            all_backing.append(canvas.create_text(int(canvas_cfg.width / 2), 65, font=('', 60), text='ASTEROID', fill='red'))
            button_centre = [int(canvas_cfg.width / 2), int(canvas_cfg.height / 2) + 50]
            all_backing.append(canvas.create_rectangle(button_centre[0] - 50, button_centre[1] - 20, button_centre[0] + 50, button_centre[1] + 20, outline='red'))
            all_backing.append(canvas.create_text(button_centre[0], button_centre[1], text='START', fill='red'))
        def close():
            for item in all_backing:
                canvas.delete(item)
        def mouse(event):
            global scene
            button_centre = [int(canvas_cfg.width / 2), int(canvas_cfg.height / 2) + 50]
            if button_centre[0] - 50 < event.x < button_centre[0] + 50 and button_centre[1] - 20 < event.y < button_centre[1] + 20:
                scene = 'game'
                graphics(['background', 'start'])
    class game:
        def __init__(self):
            global thread_refs
            thread = threading.Thread(target=scripts.game.asteroids, args=[canvas], name='Asteroid')
            thread.daemon = True
            thread.start()
            thread_refs.append(thread)
            class event: #Simulate first click to position the ship
                x = int(canvas_cfg.width / 2)
                y = 0
            scripts.game.mouse(event)
            #Start scoreboard visual thread
            thread = threading.Thread(target=scripts.game.scoreboard, name='Scoreboard')
            thread.daemon = True
            thread.start()
            thread_refs.append(thread)
            #Start powerup bar thread
            thread = threading.Thread(target=scripts.game.power_up_bar, name='Powerup')
            thread.daemon = True
            thread.start()
            thread_refs.append(thread)
            #Start health bar thread
            thread = threading.Thread(target=scripts.game.health_bar, name='Health')
            thread.daemon = True
            thread.start()
            thread_refs.append(thread)
        def background():
            pass
        def mouse(event):
            global scripts, thread_refs
            scripts.game.thread = scripts.game.thread + 1
            thread = threading.Thread(target=scripts.game.move_ship_to, args=(event.x, event.y), name='Movement Thread #' + str(scripts.game.thread))
            thread.daemon = True
            thread.start()
            thread_refs.append(thread)
        def right_mouse(event):
            global asteroids, scripts
            if scripts.game.powerup_level == 50:
                scripts.game.powerup_level = 0
                laser = canvas.create_line(scripts.game.ship_x, 0, scripts.game.ship_x, scripts.game.ship_y, fill=settings.laser.colour)
                for ast in asteroids:
                    ret = scripts.game.testforclip(ast.x, ast.y, string=True)
                    if ret == 'x':
                        canvas.delete(ast.image)
                        asteroids.remove(ast)
                time.sleep(settings.laser.flash)
                canvas.delete(laser)
                for t in range(settings.laser.times - 1): #Subtract 1 for first flash
                    laser = canvas.create_line(scripts.game.ship_x, 0, scripts.game.ship_x, scripts.game.ship_y, fill=settings.laser.colour)
                    time.sleep(settings.laser.flash)
                    canvas.delete(laser)
                    time.sleep(settings.laser.flash)
        def move_ship_to(f_x, f_y):
            try:
                global scripts
                name = threading.currentThread().getName()
                #print(name)
                start_x = scripts.game.ship_x
                start_y = scripts.game.ship_y
                if not scripts.game.ship == []:
                    for ship in scripts.game.ship:
                        canvas.delete(ship)
                series = [[], []] #x, y
                if start_x == None:
                    series = [[None, f_x], [None, f_y]]
                else:
                    series = [[f_x], [f_y]]
                    c_by = scripts.game.speed
                    if start_x > f_x:
                        c_by = 0 - scripts.game.speed
                    for i in range(start_x, f_x, c_by):
                        series[0].append(i)
                    c_by = scripts.game.speed
                    if start_y > f_y:
                        c_by = 0 - scripts.game.speed
                    for i in range(start_y, f_y, c_by):
                        series[1].append(i)
                series[0] = series[0][1:]
                series[1] = series[1][1:]
                #time.sleep(0.1)
                for index in range(0, len(series[0])):
                    x = series[0][index]
                    y = canvas_cfg.height - 50
                    scripts.game.ship_x = x
                    scripts.game.ship_y = y
                    scripts.game.ship.append(scripts.game.render_ship(canvas, x, y))
                    #canvas.update()
                    time.sleep(0.08)
                    for ship in scripts.game.ship:
                        canvas.delete(ship)
                    if not 'Movement Thread #' + str(scripts.game.thread) == name:
                        raise RuntimeError('Thread is not main') #Another movement has been started - this one must stop
                x = f_x
                y = canvas_cfg.height - 50
                scripts.game.ship_x = x
                scripts.game.ship_y = y
                scripts.game.ship.append(scripts.game.render_ship(canvas, x, y))
            except RuntimeError: #Catch close to stop an ugly message appearing
                pass
        def render_ship(canvas, x, y):
            global scripts
            if scripts.game.clip:
                colour = 'white'
            else:
                colour = scripts.game.ship_colour
            scripts.game.clip = False #Has been processed
            return canvas.create_polygon(x, y - 15, x + 5, y, x + 2, y + 5, x, y, x - 2, y + 5, x - 5, y, fill=colour, outline=colour)
        def asteroids(canvas):
            global scripts, asteroid, asteroids, score, canvas_cfg
            asteroids = []
            def render(canvas, obj):
                return canvas.create_rectangle(obj.x, obj.y, obj.x + 50, obj.y + 50, fill=obj.colour, outline=obj.colour)
            class frame:
                start = None
                end = None
                duration = None
                delay = None
                fps_data = []
                class alerts:
                    warning = None
                    counter = None
            while True:
                frame.start = time.time()
                if len(asteroids) < (score / settings.asteroids.difficulty_increment) + 4: #Cap asteroids
                    class new_asteroid:
                        colour = 'brown'
                        x = None
                        y = None
                        image = None
                        class speed:
                            x = None
                            y = None
                    new_asteroid.y = -50
                    new_asteroid.x = random.randint(0, canvas_cfg.width - 50)
                    new_asteroid.image = render(canvas, new_asteroid)
                    new_asteroid.speed.x =  random.randint(-2, 2)
                    new_asteroid.speed.y = random.randint(5, 10)
                    asteroids.append(new_asteroid)
                for item in asteroids:
                    item.y = item.y + item.speed.y
                    item.x = item.x + item.speed.x
                    canvas.delete(item.image)
                    if item.y < canvas_cfg.height and item.x < canvas_cfg.width and item.x + 50 > 0: #Make sure inside canvas borders
                        item.image = render(canvas, item)
                        if scripts.game.testforclip(item.x, item.y):
                            if scripts.game.last_clip == None:
                                clip = True
                            else:
                                clip = False
                                if scripts.game.last_clip < time.time() - settings.immunity:
                                    clip = True
                            if clip:
                                scripts.game.last_clip = time.time()
                                scripts.game.health = scripts.game.health - 1
                                scripts.game.clip = True
                            immunity = False
                            for ship in scripts.game.ship:
                                canvas.delete(ship)
                            scripts.game.ship.append(scripts.game.render_ship(canvas, scripts.game.ship_x, scripts.game.ship_y))
                        #print(index, asteroids[index].y, asteroids[index].x, sep='\t')
                    else:
                        asteroids.remove(item)
                        score = score + 1
                #This should help keep you at a stable FPS
                frame.end = time.time()
                frame.duration = frame.end - frame.start
                frame.delay = 0.07 - frame.duration
                try:
                    canvas.delete(frame.alerts.warning)
                except tk.TclError:
                    pass
                try:
                    canvas.delete(frame.alerts.counter)
                except tk.TclError:
                    pass
                try:
                    if len(frame.fps_data) > settings.asteroids.fps_smoothing: 
                        frame.fps_data.pop(0)
                    frame.fps_data.append(1 / frame.duration)
                    total = 0
                    for data in frame.fps_data:
                        total = total + data
                    average = total / len(frame.fps_data)
                    if average > 60:
                        colour = 'green'
                    elif average > 20:
                        colour = 'yellow'
                    else:
                        colour = 'red'
                    my_fps = str(round(average, 2))
                except ZeroDivisionError:
                    my_fps = 'HIGH' #Apparently - the loop took 0 seconds - this has happened, so this is my error catching
                    colour = 'green'
                frame.alerts.counter = canvas.create_text(canvas_cfg.width - (10 + len(my_fps)), 10, justify='right', text=my_fps, fill=colour)
                if frame.delay > 0:
                    time.sleep(frame.delay)
                else:
                    #print('FRAME WARNING') #Frames are too low
                    frame.alerts.warning = canvas.create_text(canvas_cfg.width - 25, canvas_cfg.height - 10, justify='right', text='Low FPS', fill='red')
        def scoreboard(): #Score visual updater
            global score
            oldscore = score + 1 #Make sure that they are different
            scoreboard_image = None
            while True:
                while oldscore == score: #until not statement
                    time.sleep(0.1) #pass drains CPU (I think because it is too fast and has to check the condition loads) - this doesn't
                oldscore = score
                if not scoreboard_image == None:
                    canvas.delete(scoreboard_image)
                scoreboard_image = canvas.create_text(int(canvas_cfg.width / 2), 15, text=str(score), fill='red', font=('', 20))
        def testforclip(asteroid_x, asteroid_y, asteroid_size=50, ship_xp=5, ship_xm=5, ship_yp=15, ship_ym=5, string=False): #p is change positive, m is change negative
            x = scripts.game.ship_x
            y = scripts.game.ship_y
            if not settings.asteroids.clip: #No clip setting
                return Falsehealth_bar
            xclip, yclip = False, False #Set up clipping variables
            if asteroid_x - ship_xp > x > asteroid_x + asteroid_size + ship_xm or asteroid_x - ship_xp < x < asteroid_x + asteroid_size + ship_xm:
                xclip = True
            if asteroid_y - ship_yp > y > asteroid_y + asteroid_size + ship_ym or asteroid_y - ship_yp < y < asteroid_y + asteroid_size + ship_ym:
                yclip = True
            if xclip and yclip: #On clip
                #print('clip' + str(random.randint(1, 50) * '-'))
                if string:
                    return 'both'
                else:
                    return True
            if string:
                if xclip and not yclip:
                    return 'x'
                elif yclip and not xclip:
                    return 'y'
                else:
                    return 'none'
            else:
                return False
        def power_up_bar():
            global scripts
            old_level = scripts.game.powerup_level + 1
            image = canvas.create_rectangle(10, canvas_cfg.height - 10, 10 + scripts.game.powerup_level, canvas_cfg.height - 10, fill='red', outline='red')
            while True:
                if scripts.game.powerup_level < 50:
                    scripts.game.powerup_level = scripts.game.powerup_level + 1
                old_level = scripts.game.powerup_level
                canvas.delete(image)
                if scripts.game.powerup_level == 50:
                    colour = 'green'
                elif scripts.game.powerup_level > 25:
                    colour = 'orange'
                else:
                    colour = 'red'
                image = canvas.create_rectangle(10, canvas_cfg.height - 10, 10 + scripts.game.powerup_level, canvas_cfg.height - 10, fill=colour, outline=colour)
                time.sleep(0.05)
        def health_bar():
            global scripts
            old_level = scripts.game.health + 1
            image = canvas.create_rectangle(10, canvas_cfg.height - 20, 10 + scripts.game.health, canvas_cfg.height - 20, fill='red', outline='red')
            while True:
                while old_level == scripts.game.health:
                    time.sleep(0.1)
                old_level = scripts.game.health
                canvas.delete(image)
                if scripts.game.health == 0:
                        print('Game over')
                else:
                    if scripts.game.health == 5:
                        colour = 'green'
                    elif scripts.game.health > 2:
                        colour = 'orange'
                    else:
                        colour = 'red'
                    image = canvas.create_rectangle(10, canvas_cfg.height - 20, 10 + (scripts.game.health * 10), canvas_cfg.height - 20, fill=colour, outline=colour)
        ship = []
        ship_x = None
        ship_y = None
        close_movement = False
        speed = 10
        thread = 0
        ship_colour = 'red'
        clip = False
        last_clip = None
        powerup_level = 0
        health = 5

end = False
scenes = {'game':{'background':'#ff8742',
                   'script':scripts.game},
          'start':{'background':'snow1',
                   'script':scripts.start}}
scene = 'start'
old = None

class graphics:
    def __init__(self, refresh):
        global old
        for item in refresh:
            if item == 'background':
                scenes[scene]['script'].background()
                canvas.config(background=scenes[scene]['background'])
            elif item == 'start':
                if not old == None:
                    scenes[old]['script'].close()
                old = scene
                thread = threading.Thread(target=scenes[scene]['script'])
                thread.daemon = True
                thread.start()
                thread_refs.append(thread)
    class mouse:
        def down(event):
            if event.widget == canvas:
                global graphics
                scenes[scene]['script'].mouse(event)
                graphics.mouse.x = event.x
                graphics.mouse.y = event.y
        def left_down(event):
            if event.widget == canvas:
                global graphics
                thread = threading.Thread(target=scenes[scene]['script'].right_mouse, args=[event])
                thread.daemon = True
                thread.start()
                graphics.mouse.left_x = event.x
                graphics.mouse.left_y = event.y
        x = None
        y = None
        left_x = None
        left_y = None
    sprites = []

root.bind('<Button-1>', graphics.mouse.down)
root.bind('<Button-3>', graphics.mouse.left_down)

graphics(['background', 'start'])

root.mainloop()

for thread in thread_refs: #Unfortunately doesn't do anything
    pass #thread.close()
