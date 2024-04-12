# -*- coding: utf-8 -*-
"""
Created on Tue Mar 19 03:46:30 2024

@author: msi
"""

import sys
import random
import time
import numpy as np
from PyQt5.QtWidgets import QApplication, QLineEdit, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QFileDialog, QGraphicsScene, QGraphicsView, QMessageBox, QLabel
from PyQt5.QtGui import QColor, QPen, QPolygonF, QFont, QIcon
from PyQt5.QtCore import Qt, QPointF

class Agent:
    life_time = None
    def __init__(self):
        self.bump = False
        self.dirty = False

    class ActionType:
        UP = 0
        DOWN = 1
        LEFT = 2
        RIGHT = 3
        SUCK = 4
        IDLE = 5

    def perceive(self, env):
        self.bump = env.is_just_bump()
        self.dirty = env.is_current_pos_dirty()

    def think(self, OBS_ARRAY, env):
        if self.dirty:
            return self.ActionType.SUCK
        else:
            while True:
                action = random.choice([self.ActionType.UP, self.ActionType.DOWN,
                                        self.ActionType.LEFT, self.ActionType.RIGHT])
                if not OBS_ARRAY[env.agent_y, env.agent_x, action]:
                    return action
                
def action_string(action):
    if action == Agent.ActionType.UP:
        return "UP"
    elif action == Agent.ActionType.DOWN:
        return "DOWN"
    elif action == Agent.ActionType.LEFT:
        return "LEFT"
    elif action == Agent.ActionType.RIGHT:
        return "RIGHT"
    elif action == Agent.ActionType.SUCK:
        return "SUCK"
    elif action == Agent.ActionType.IDLE:
        return "IDLE"
    else:
        return "???"


class Environment:
    MAZE_SIZE = 10
    OBSTACLE = -1
    MAP_ROAD = '-'
    MAP_OBSTACLE = 'O'
    CELL_SIZE = 40
    AGENT_SIZE = CELL_SIZE * 0.8
    OBSTACLES_ARRAY = np.full((MAZE_SIZE,MAZE_SIZE,4),False)
    RED_OBSTACLES = np.full((MAZE_SIZE,MAZE_SIZE), False)
    def __init__(self, infile):
        infile.readline()
        line = infile.readline().strip().split()
        self.agent_x = int(line[0])
        self.agent_y = int(line[1])
        self.dirty_prob = float(line[2])
        self.random_seed = int(line[3])

        self.maze = [[0]*self.MAZE_SIZE for _ in range(self.MAZE_SIZE)]
        self.bump = False
        self.pre_action = Agent.ActionType.IDLE
    
        for row in range(self.MAZE_SIZE):
            line = infile.readline().strip().split()
            for col in range(0, len(line), 1):
                if line[col] == self.MAP_ROAD:
                    self.maze[row][col] = 0
                elif line[col] == self.MAP_OBSTACLE:
                    self.maze[row][col] = self.OBSTACLE
                else:
                    print(f"{line[col]} is an unknown symbol in agent.map!")
                    exit(1)

    def is_current_pos_dirty(self):
        return self.maze[self.agent_y][self.agent_x] > 0
    
    def is_just_bump(self):
        return self.bump
    
    def seed(self):
        return self.random_seed

    def dirt_amount(self, row, col):
        if self.maze[row][col] == self.OBSTACLE:
            return 0
        else:
            return self.maze[row][col]
        
# random.random(): Returns a random float number between 0 and 1
    def change(self):
        for row in range(self.MAZE_SIZE):
            for col in range(self.MAZE_SIZE):
                if self.maze[row][col] != self.OBSTACLE and random.uniform(0,1) < self.dirty_prob:
                    self.maze[row][col] += 1

    def accept_action(self, action):
        self.bump = False

        if action == Agent.ActionType.SUCK:
            if self.maze[self.agent_y][self.agent_x] > 0:
                self.maze[self.agent_y][self.agent_x] -= 1
        else:
            dx, dy = 0, 0
            if action == Agent.ActionType.UP:
                dy = -1
            elif action == Agent.ActionType.DOWN:
                dy = 1
            elif action == Agent.ActionType.LEFT:
                dx = -1
            elif action == Agent.ActionType.RIGHT:
                dx = 1

            new_x = self.agent_x + dx
            new_y = self.agent_y + dy

            if self.maze[new_y][new_x] == self.OBSTACLE:
                self.bump = True
                self.OBSTACLES_ARRAY[self.agent_y, self.agent_x, action] = True
                self.RED_OBSTACLES[new_y, new_x] = True  # Mark obstacle as red
            else:
                self.agent_x = new_x
                self.agent_y = new_y

        self.pre_action = action

        


    def show(self, scene):
        scene.clear()
        # Draw map
        self.draw_map(scene)
        # Draw agent
        self.draw_agent(scene)
        
    def draw_map(self, scene):
        for i, row in enumerate(self.maze):
            for j, cell in enumerate(row):
                if self.RED_OBSTACLES[i, j]:  # Check if obstacle shouldd be red
                    color = QColor(Qt.red)
                else:
                    dirty_color = 255 - self.maze[i][j] * 10
                    color = QColor.fromRgb(dirty_color, dirty_color, dirty_color
                                           ) if cell != self.OBSTACLE else QColor(Qt.darkCyan)
                scene.addRect(j * self.CELL_SIZE, i * self.CELL_SIZE, self.CELL_SIZE,
                              self.CELL_SIZE, QPen(color), color)
    
    def draw_agent(self, scene):
        agent_color = QColor(Qt.green) if not self.bump else QColor(Qt.red)
        gap = (self.CELL_SIZE - self.AGENT_SIZE) / 2
        if self.pre_action == Agent.ActionType.IDLE:
            scene.addRect(self.agent_x * self.CELL_SIZE + gap,
                          self.agent_y * self.CELL_SIZE + gap,
                          self.AGENT_SIZE, self.AGENT_SIZE, QPen(agent_color), agent_color)
            
        elif self.pre_action == Agent.ActionType.SUCK:
            agent_color = QColor.fromRgb(255,165,0)
            scene.addRect(self.agent_x * self.CELL_SIZE + gap,
                          self.agent_y * self.CELL_SIZE + gap,
                          self.AGENT_SIZE, self.AGENT_SIZE, QPen(agent_color), agent_color)
            
        elif self.pre_action == Agent.ActionType.UP:
            agent_polygon = QPolygonF([
                QPointF(self.agent_x * self.CELL_SIZE + self.CELL_SIZE / 2, self.agent_y * self.CELL_SIZE + gap),
                QPointF(self.agent_x * self.CELL_SIZE  + gap, self.agent_y * self.CELL_SIZE + self.CELL_SIZE  - gap),
                QPointF(self.agent_x * self.CELL_SIZE + self.CELL_SIZE  - gap, self.agent_y * self.CELL_SIZE + self.CELL_SIZE  - gap)
            ])
            scene.addPolygon(agent_polygon, QPen(agent_color), QColor(agent_color))
            
        elif self.pre_action == Agent.ActionType.RIGHT:
            agent_polygon = QPolygonF([
                QPointF(self.agent_x * self.CELL_SIZE + gap, self.agent_y * self.CELL_SIZE + gap),
                QPointF(self.agent_x * self.CELL_SIZE + gap, self.agent_y * self.CELL_SIZE + self.CELL_SIZE - gap),
                QPointF(self.agent_x * self.CELL_SIZE + self.CELL_SIZE - gap, self.agent_y * self.CELL_SIZE + self.CELL_SIZE/2)
            ])
            scene.addPolygon(agent_polygon, QPen(agent_color), QColor(agent_color))
            
        elif self.pre_action == Agent.ActionType.DOWN:
            agent_polygon = QPolygonF([
                QPointF(self.agent_x * self.CELL_SIZE + gap, self.agent_y * self.CELL_SIZE + gap),
                QPointF(self.agent_x * self.CELL_SIZE + self.CELL_SIZE - gap, self.agent_y * self.CELL_SIZE + gap),
                QPointF(self.agent_x * self.CELL_SIZE + self.CELL_SIZE/2, self.agent_y * self.CELL_SIZE + self.CELL_SIZE - gap)
            ])
            scene.addPolygon(agent_polygon, QPen(agent_color), QColor(agent_color))
            
        elif self.pre_action == Agent.ActionType.LEFT:
            agent_polygon = QPolygonF([
                QPointF(self.agent_x * self.CELL_SIZE + self.CELL_SIZE - gap, self.agent_y * self.CELL_SIZE + gap),
                QPointF(self.agent_x * self.CELL_SIZE + self.CELL_SIZE - gap, self.agent_y * self.CELL_SIZE + self.CELL_SIZE - gap),
                QPointF(self.agent_x * self.CELL_SIZE + gap, self.agent_y * self.CELL_SIZE + self.CELL_SIZE/2)
            ])
            scene.addPolygon(agent_polygon, QPen(agent_color), QColor(agent_color))
  

##########################################################################################
class Evaluator:

    def __init__(self):
        self._dirty_degree = 0
        self._consumed_energy = 0

    def dirty_degree(self):
        return self._dirty_degree

    def consumed_energy(self):
        return self._consumed_energy

    def eval(self, action, env):
        if action == Agent.ActionType.SUCK:
            self._consumed_energy += 2
        elif action != Agent.ActionType.IDLE:
            self._consumed_energy += 1
            
        self._dirty_degree = 0
        for row in range(Environment.MAZE_SIZE):
            for col in range(Environment.MAZE_SIZE):
                da = env.dirt_amount(row, col)
                self._dirty_degree += da
                
########################################################################################
'''
class RandomNumberGenerator:
    def __init__(self, seed):
        random.seed(seed)
        self.rand_num = [random.uniform(0, 1) for _ in range(Environment.MAZE_SIZE * Environment.MAZE_SIZE * Agent.life_time)]
        self.index = 0

    def random_value(self):
        if self.index >= len(self.rand_num):
            print("Insufficient random values!")
            exit(1)
        value = self.rand_num[self.index]
        self.index += 1
        return value
'''
##########################################################################################
class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Rational Agent")
        self.setGeometry(100, 100, 700, 700)

        # Create main layout
        main_layout = QVBoxLayout()

        # Create top layout and split it into left and right
        top_layout = QHBoxLayout()

        self.left_widget = QWidget()
        self.left_widget.setStyleSheet("background-color: lightblue;")
        left_layout = QVBoxLayout()
        self.left_widget.setLayout(left_layout)

        self.right_widget = QWidget()
        self.right_widget.setStyleSheet("background-color: lightgreen;")
        right_layout = QVBoxLayout()
        self.right_widget.setLayout(right_layout)

        # Creat controls
        self.load_button = QPushButton("Select Map")
        self.load_button.clicked.connect(self.select_map)
        self.do_one_step_button = QPushButton("Do One Step")
        self.do_one_step_button.clicked.connect(self.do_one_step)
        self.change_parameters_button = QPushButton("Change")
        self.change_parameters_button.clicked.connect(self.change_parameters)
        self.do_one_run_button = QPushButton("Do One Run")
        self.do_one_run_button.clicked.connect(self.do_one_run)
        self.next_run_button = QPushButton("Next Run")
        self.next_run_button.clicked.connect(self.next_run)
        self.do_all_runs_button = QPushButton("Do All runs")
        self.do_all_runs_button.clicked.connect(self.do_all_runs)
        self.play_again_button = QPushButton("Play Again")
        self.play_again_button.clicked.connect(self.play_again)
        self.label_runs_number = QLabel("Runs:")
        self.text_runs = QLineEdit('10')
        self.text_runs.setStyleSheet('background-color: white;')
        self.text_runs.setPlaceholderText('Enter Runs #')
        self.label_life_time = QLabel("Life Time:")
        self.text_life_time = QLineEdit('100')
        self.text_life_time.setStyleSheet('background-color: white;')
        self.text_life_time.setPlaceholderText('Enter Life Time')
        
        # Create a layout for controls
        control_layout = QVBoxLayout()
        control_layout.setAlignment(Qt.AlignTop)
        control_layout.addWidget(self.load_button)
        control_layout.addSpacing(15) # Add 15 pixel spacing between Controls
        control_layout.addWidget(self.label_runs_number)
        control_layout.addWidget(self.text_runs)
        control_layout.addSpacing(5)
        control_layout.addWidget(self.label_life_time)
        control_layout.addWidget(self.text_life_time)
        control_layout.addSpacing(5)
        control_layout.addWidget(self.change_parameters_button)
        control_layout.addSpacing(40)
        control_layout.addWidget(self.do_one_step_button)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.next_run_button)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.next_run_button)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.do_one_run_button)
        control_layout.addSpacing(10)
        control_layout.addWidget(self.do_all_runs_button)
        control_layout.addSpacing(15)
        control_layout.addWidget(self.play_again_button)

        # Add control layout to the right layout
        self.right_widget.layout().addLayout(control_layout)

        # Add widgets to main layout
        top_layout.addWidget(self.left_widget, 4)
        top_layout.addWidget(self.right_widget, 1)
        
        
        # Create bottom layout
        bottom_widget = QWidget()
        bottom_widget.setStyleSheet("background-color: lightyellow;")
        
        # Label to show data while vacuum working
        self.run_label = QLabel("")
        self.total_label = QLabel("")
        
        font = QFont()
        font.setPointSize(12)
        font.setFamily("Times New Roman")
        self.run_label.setFont(font)
        self.run_label.setStyleSheet("color: rgb(0,0,255)")
        self.total_label.setFont(font)
        self.total_label.setStyleSheet("color: rgb(0,0,0)")
        
        bottom_layout = QHBoxLayout()
        bottom_layout.addWidget(self.run_label)
        bottom_layout.addSpacing(20)
        bottom_layout.addWidget(self.total_label)
        bottom_widget.setLayout(bottom_layout)
        
        
        # Add bottom widget and top layout to the main layout
        main_layout.addLayout(top_layout, 6)
        main_layout.addWidget(bottom_widget, 2)

        # Set the central widget
        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        # Initialize QGraphicsScene and QGraphicsView for drawing
        self.scene = QGraphicsScene()
        self.view = QGraphicsView(self.scene)
        self.left_widget.layout().addWidget(self.view)
        
        # set the window icon
        self.setWindowIcon(QIcon('cleaner.jpg'))
        
        self.env=None # Environment
        self.agent=Agent() # Agent
        self.evaluator=Evaluator() # Evaluator
        self.action=Agent.ActionType.IDLE # Initial agent status is IDLE 

        self.runs = 5
        self.current_run = 0
        self.current_time=0
        self.run_dirty=0
        self.run_energy=0
        
        self.total_dirty=0
        self.total_energy=0
        
        self.file_path=None

    def change_parameters(self):
        self.runs = int(self.text_runs.text())
        self.agent.life_time = int(self.text_life_time.text())

    def select_map(self):
        file_dialog = QFileDialog()
        file_dialog.setFileMode(QFileDialog.AnyFile)
        if file_dialog.exec_():
            self.file_path = file_dialog.selectedFiles()[0]
            self.new_game()
    
    def play_again(self):
        if self.file_path is None:
            self.select_map()
        self.load_button.setEnabled(True)
        self.next_run_button.setEnabled(True)
        self.do_one_step_button.setEnabled(True)
        self.do_one_run_button.setEnabled(True)
        self.do_all_runs_button.setEnabled(True)
        self.text_runs.setEnabled(True)
        self.text_life_time.setEnabled(True)
        self.new_game()
    
    def do_all_runs(self):
        if self.file_path is None:
            self.select_map()
        self.new_game()
        while self.current_run < self.runs:
            self.do_one_run()
            QApplication.processEvents()
            time.sleep(1.5)
        else:
            self.play_again_button.setEnabled(True)
    
    def do_one_run(self):
        if self.file_path is None:
            self.select_map()
        if self.current_time != 0:
            self.next_run()
        while self.current_time < self.agent.life_time:
            self.do_one_step()
            QApplication.processEvents()
            time.sleep(0.05)
            
    def do_one_step(self):
        if self.current_time < self.agent.life_time:
            self.env.change()
            self.agent.perceive(self.env)
            self.action = self.agent.think(self.env.OBSTACLES_ARRAY,self.env)
            self.env.accept_action(self.action)
            self.env.show(self.scene)
            self.evaluator.eval(self.action, self.env)
            self.current_time +=1
            self.show_score()
 
        else:
            self.show_score()



    def show_score(self):
        self.run_dirty = self.evaluator.dirty_degree()
        self.run_energy = self.evaluator.consumed_energy()
        
        # self.run_label.setText("<font face='Times New Roman' size='6' color = 'red'>Text to show:<br><b>after clicking 'Do One Step' button</b></font>.")
        bump = "BUMP" if self.env.is_just_bump() else ""
        action_str = action_string(self.action) +" " + bump
        self.run_label.setText(f"Current Run: {self.current_run}\t"
                               f"Current Time: {self.current_time}\n"
                               f"Action: {action_str}\n"
                               f"Dirty Degree: {self.run_dirty}\n"
                               f"Consumed Energy: {self.run_energy}")
        
        if self.current_time >= self.agent.life_time:
            self.total_dirty += self.run_dirty
            self.total_energy += self.run_energy
            avg_dirty = self.total_dirty//(self.current_run)
            avg_energy = self.total_energy//(self.current_run)
            self.total_label.setText(f"Completed Runs: {self.current_run}\n"
                                     f"Total Dirty Degree: {self.total_dirty},  Total Consumed Energy: {self.total_energy}\n"
                                     f"Average Dirty Degree: {avg_dirty},  Average Consumed Energy: {avg_energy}")
        if self.current_run > self.runs:
            self.load_button.setEnabled(False)
            self.next_run_button.setEnabled(False)
            self.do_one_step_button.setEnabled(False)
            self.do_one_run_button.setEnabled(False)
            self.do_all_runs_button.setEnabled(False)
            
    def next_run(self):
        if self.current_run < self.runs:
            try:
                with open(self.file_path, 'r') as file:
                    self.current_time=0
                    self.run_dirty=0
                    self.run_energy=0
                    self.agent=Agent()
                    self.agent.life_time = int(self.text_life_time.text())
                    self.env = Environment(file)
                    self.env.show(self.scene)
                    random.seed(self.env.seed()+self.current_run)
                    self.evaluator = Evaluator()
                    self.action = Agent.ActionType.IDLE
                    self.evaluator.eval(self.action, self.env)
                    self.current_run +=1
                    self.show_score()
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))
        else:
            pass

        
    def new_game(self):
        self.runs = int(self.text_runs.text())
        self.current_run=0
        self.total_dirty=0
        self.total_energy=0
        self.next_run()
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
