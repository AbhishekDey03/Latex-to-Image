import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.patches import Ellipse, Rectangle, Polygon
from matplotlib.lines import Line2D
from matplotlib.text import Text
from collections import deque
import numpy as np
import sys

class DrawToLatexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Draw to LaTeX Vector Code")

        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Canvas setup
        self.fig, self.ax = plt.subplots()
        self.canvas = FigureCanvasTkAgg(self.fig, master=root)
        self.canvas.get_tk_widget().pack(side=tk.LEFT, fill=tk.BOTH, expand=1)
        self.ax.set_aspect('equal', adjustable='box')
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 10)
        self.ax.axis('off')

        # Controls frame
        controls_frame = ttk.Frame(root)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y)

        self.shape_var = tk.StringVar(value='Line')
        shapes = ['Line', 'Arrow Line', 'Ellipse', 'Rectangle', 'Text', 'Select', 'Erase', 'Cone', 'Upside-down Cone']
        for shape in shapes:
            ttk.Radiobutton(controls_frame, text=shape, variable=self.shape_var, value=shape).pack(anchor=tk.W)

        self.color_var = tk.StringVar(value='black')
        colors = ['white', 'black', 'red', 'green', 'blue', 'cyan', 'magenta', 'yellow']
        ttk.Label(controls_frame, text="Choose Color").pack(pady=5)
        color_menu = ttk.OptionMenu(controls_frame, self.color_var, *colors)
        color_menu.pack(pady=5)

        self.linewidth = 1

        ttk.Button(controls_frame, text="Clear", command=self.clear_canvas).pack(pady=5)
        ttk.Button(controls_frame, text="Generate LaTeX", command=self.generate_latex).pack(pady=5)

        self.canvas.mpl_connect('button_press_event', self.on_click)
        self.canvas.mpl_connect('motion_notify_event', self.on_motion)
        self.canvas.mpl_connect('button_release_event', self.on_release)

        self.start_x = None
        self.start_y = None
        self.current_shape = None
        self.textbox = None
        self.selected_shape = None
        self.selection_rectangle = None
        self.history = deque(maxlen=20)
        self.is_moving = False
        self.arrowheads = []

        self.root.bind("<Control-z>", self.undo_last_action)
        self.canvas.get_tk_widget().bind("<Key>", self.on_text_key_press)
        self.canvas.get_tk_widget().focus_set()

    def on_closing(self):
        self.root.quit()
        self.root.destroy()
        sys.exit(0)

    def on_click(self, event):
        """Handle mouse click events for drawing and selecting shapes."""
        if event.inaxes != self.ax:
            return
        if self.shape_var.get() == 'Select':
            if self.selected_shape:
                self.deselect_shape()
            else:
                self.select_shape(event)
                if self.selected_shape:
                    self.draw_selection_rectangle()
        elif self.shape_var.get() == 'Erase':
            self.erase_shape(event)
        else:
            self.start_x, self.start_y = event.xdata, event.ydata
            shape = self.shape_var.get()
            self.color = self.color_var.get()
            if shape == 'Ellipse':
                self.current_shape = Ellipse((self.start_x, self.start_y), 0.1, 0.1, edgecolor=self.color, facecolor='none', linewidth=self.linewidth)
            elif shape == 'Rectangle':
                self.current_shape = Rectangle((self.start_x, self.start_y), 0.1, 0.1, edgecolor=self.color, facecolor='none', linewidth=self.linewidth)
            elif shape == 'Line':
                self.current_shape = Line2D([self.start_x, self.start_x], [self.start_y, self.start_y], color=self.color, linewidth=self.linewidth)
                self.ax.add_line(self.current_shape)
            elif shape == 'Arrow Line':
                self.current_shape = Line2D([self.start_x, self.start_x], [self.start_y, self.start_y], color=self.color, linewidth=self.linewidth)
                self.ax.add_line(self.current_shape)
            elif shape == 'Text':
                self.textbox = self.ax.text(self.start_x, self.start_y, "", color=self.color, fontsize=12, bbox=dict(facecolor='white', edgecolor='none', boxstyle='round,pad=0.5'))
                self.current_shape = self.textbox
                self.canvas.get_tk_widget().focus_set()
            elif shape == 'Cone' or shape == 'Upside-down Cone':
                # Draw a placeholder ellipse to be adjusted during motion
                self.current_shape = Ellipse((self.start_x, self.start_y), 0.1, 0.05, edgecolor=self.color, facecolor='none', linewidth=self.linewidth)
                self.ax.add_patch(self.current_shape)
            if shape in ['Ellipse', 'Rectangle']:
                self.ax.add_patch(self.current_shape)
            self.canvas.draw()

    def on_motion(self, event):
        if not event.inaxes:
            return
        if self.is_moving and self.selected_shape:
            dx = event.xdata - self.start_x
            dy = event.ydata - self.start_y
            self.move_shape(self.selected_shape, dx, dy)
            self.start_x, self.start_y = event.xdata, event.ydata
            self.update_selection_rectangle()
            self.canvas.draw()
        elif self.current_shape:
            if self.shape_var.get() in ['Ellipse', 'Cone', 'Upside-down Cone']:
                width = abs(event.xdata - self.start_x)
                height = abs(event.ydata - self.start_y)
                self.current_shape.width = width
                self.current_shape.height = height
                self.current_shape.center = (self.start_x + width / 2, self.start_y)
            elif self.shape_var.get() == 'Rectangle':
                width = event.xdata - self.start_x
                height = event.ydata - self.start_y
                self.current_shape.set_width(width)
                self.current_shape.set_height(height)
            elif self.shape_var.get() in ['Line', 'Arrow Line']:
                self.current_shape.set_data([self.start_x, event.xdata], [self.start_y, event.ydata])
            self.canvas.draw()

    def on_release(self, event):
        if self.current_shape and self.shape_var.get() in ['Cone', 'Upside-down Cone']:
            width = abs(event.xdata - self.start_x)
            height = abs(event.ydata - self.start_y)

            cx, cy = self.start_x + width / 2, self.start_y  # Center of the ellipse

            # Adjust the factor for the apex to make the cone appear natural
            if self.shape_var.get() == 'Cone':
                apex_y = self.start_y + height * 3.
                angle_offset = np.arctan2(height, width / 2)
            else:
                apex_y = self.start_y - height * 3.
                angle_offset = np.arctan2(height, width / 2)

            # Increasing angle_offset to make base points closer to the edges
            angle_adjustment = 0.4 # Adjust this factor to spread the base points further apart
            left_angle = angle_offset * angle_adjustment
            right_angle = angle_offset * angle_adjustment

            # Calculate base points using adjusted angles
            #- 0.04 * height
            left_base = (cx - (width / 2) * np.cos(left_angle), cy - (height / 2) * np.sin(left_angle) if self.shape_var.get() == 'Upside-down Cone' else (height / 2) * np.sin(left_angle))
            right_base = (cx + (width / 2) * np.cos(right_angle), cy  - (height / 2) * np.sin(right_angle) if self.shape_var.get() == 'Upside-down Cone' else (height / 2) * np.sin(right_angle))

            self.draw_cone(left_base, right_base, (cx, apex_y), self.color)

        if self.current_shape and self.shape_var.get() == 'Arrow Line':
            self.add_arrowhead(self.current_shape)

        if self.current_shape and self.shape_var.get() != 'Select':
            self.history.append(self.current_shape)
        self.current_shape = None
        self.is_moving = False
        self.canvas.draw()

    def draw_cone(self, left_base, right_base, apex, color):
        line_left = Line2D([left_base[0], apex[0]], [left_base[1], apex[1]], color=color, linewidth=self.linewidth)
        line_right = Line2D([right_base[0], apex[0]], [right_base[1], apex[1]], color=color, linewidth=self.linewidth)
        self.ax.add_line(line_left)
        self.ax.add_line(line_right)
        self.history.append(line_left)
        self.history.append(line_right)

    def on_text_key_press(self, event):
        """Handle key press events for text input."""
        if self.shape_var.get() == 'Text' and self.textbox:
            if event.keysym == 'Return':
                self.textbox = None
            elif event.keysym == 'BackSpace':
                self.textbox.set_text(self.textbox.get_text()[:-1])
            else:
                self.textbox.set_text(self.textbox.get_text() + event.char)
            self.canvas.draw()

    def undo_last_action(self, event=None):
        """Undo the last action performed."""
        if self.history:
            shape = self.history.pop()
            shape.remove()
            self.canvas.draw()

    def select_shape(self, event):
        """Select a shape under the mouse pointer."""
        self.selected_shape = None
        min_distance = float('inf')
        click_point = (event.xdata, event.ydata)

        for shape in self.ax.patches + self.ax.lines + self.ax.texts + self.arrowheads:
            if isinstance(shape, Ellipse):
                distance = self.point_to_ellipse_distance(click_point, shape)
            elif isinstance(shape, Rectangle):
                distance = self.point_to_rectangle_distance(click_point, shape)
            elif isinstance(shape, Line2D):
                distance = self.point_to_line_distance(click_point, shape)
            elif isinstance(shape, Polygon):
                distance = self.point_to_polygon_distance(click_point, shape)
            elif isinstance(shape, Text):
                distance = self.point_to_text_distance(click_point, shape)
            if distance < min_distance:
                min_distance = distance
                self.selected_shape = shape

        if isinstance(self.selected_shape, (Ellipse, Rectangle, Line2D, Polygon)):
            self.start_x, self.start_y = event.xdata, event.ydata
            self.is_moving = True
        elif isinstance(self.selected_shape, Text):
            bbox = self.selected_shape.get_window_extent(self.canvas.get_renderer())
            if bbox.contains(event.x, event.y):
                self.start_x, self.start_y = event.xdata, event.ydata
                self.is_moving = True

    def erase_shape(self, event):
        """Erase a shape under the mouse pointer."""
        min_distance = float('inf')
        shape_to_erase = None
        click_point = (event.xdata, event.ydata)

        for shape in self.ax.patches + self.ax.lines + self.ax.texts + self.arrowheads:
            if isinstance(shape, Ellipse):
                distance = self.point_to_ellipse_distance(click_point, shape)
            elif isinstance(shape, Rectangle):
                distance = self.point_to_rectangle_distance(click_point, shape)
            elif isinstance(shape, Line2D):
                distance = self.point_to_line_distance(click_point, shape)
            elif isinstance(shape, Polygon):
                distance = self.point_to_polygon_distance(click_point, shape)
            elif isinstance(shape, Text):
                distance = self.point_to_text_distance(click_point, shape)
            if distance < min_distance and distance < 0.2:
                min_distance = distance
                shape_to_erase = shape
        if shape_to_erase:
            shape_to_erase.remove()
            if shape_to_erase in self.arrowheads:
                self.arrowheads.remove(shape_to_erase)
            self.canvas.draw()

    def deselect_shape(self):
        """Deselect the currently selected shape."""
        self.selected_shape = None
        self.is_moving = False
        if self.selection_rectangle and self.selection_rectangle in self.ax.patches:
            self.selection_rectangle.remove()
            self.selection_rectangle = None
        self.canvas.draw_idle()

    def point_to_ellipse_distance(self, point, ellipse):
        """Calculate the distance from a point to the edge of an ellipse."""
        px, py = point
        cx, cy = ellipse.center
        rx, ry = ellipse.width / 2, ellipse.height / 2
        return np.sqrt((px - cx) ** 2 / rx ** 2 + (py - cy) ** 2 / ry ** 2)

    def point_to_rectangle_distance(self, point, rect):
        """Calculate the distance from a point to the edge of a rectangle."""
        px, py = point
        x0, y0 = rect.xy
        x1, y1 = x0 + rect.get_width(), y0
        x2, y2 = x1, y0 + rect.get_height()
        x3, y3 = x0, y2
        return min(abs(px - x0), abs(px - x1), abs(py - y0), abs(py - y1))

    def point_to_line_distance(self, point, line):
        """Calculate the distance from a point to a line."""
        px, py = point
        x0, y0 = line.get_data()[0][0], line.get_data()[1][0]
        x1, y1 = line.get_data()[0][1], line.get_data()[1][1]
        return np.abs(np.cross([x1 - x0, y1 - y0], [x0 - px, y0 - py]) / np.linalg.norm([x1 - x0, y1 - y0]))

    def point_to_polygon_distance(self, point, polygon):
        """Calculate the distance from a point to a polygon."""
        poly_points = polygon.get_xy()
        min_distance = float('inf')
        for p1, p2 in zip(poly_points, poly_points[1:] + [poly_points[0]]):
            line_vec = np.array(p2) - np.array(p1)
            point_vec = np.array(point) - np.array(p1)
            proj = np.dot(point_vec, line_vec) / np.dot(line_vec, line_vec)
            if proj < 0:
                closest_point = np.array(p1)
            elif proj > 1:
                closest_point = np.array(p2)
            else:
                closest_point = np.array(p1) + proj * line_vec
            distance = np.linalg.norm(point - closest_point)
            if distance < min_distance:
                min_distance = distance
        return min_distance

    def point_to_text_distance(self, point, text):
        """Calculate the distance from a point to a text object."""
        tx, ty = text.get_position()
        return ((point[0] - tx) ** 2 + (point[1] - ty) ** 2) ** 0.5

    def move_shape(self, shape, dx, dy):
        """Move a shape by a given delta in x and y directions."""
        if isinstance(shape, Ellipse):
            shape.center = (shape.center[0] + dx, shape.center[1] + dy)
        elif isinstance(shape, Rectangle):
            shape.set_xy((shape.xy[0] + dx, shape.xy[1] + dy))
        elif isinstance(shape, Line2D):
            x_data, y_data = shape.get_data()
            shape.set_data([x_data[0] + dx, x_data[1] + dx], [y_data[0] + dy, y_data[1] + dy])
        elif isinstance(shape, Polygon):
            shape.set_xy([(x + dx, y + dy) for x, y in shape.get_xy()])
        elif isinstance(shape, Text):
            tx, ty = shape.get_position()
            shape.set_position((tx + dx, ty + dy))

    def change_selected_shape_color(self, color):
        """Change the color of the selected shape."""
        if isinstance(self.selected_shape, (Ellipse, Rectangle)):
            self.selected_shape.set_edgecolor(color)
        elif isinstance(self.selected_shape, Line2D):
            self.selected_shape.set_color(color)
        elif isinstance(self.selected_shape, Polygon):
            self.selected_shape.set_color(color)
        elif isinstance(self.selected_shape, Text):
            self.selected_shape.set_color(color)

    def snap_to_closest(self, line, event):
        """Snap the end of the line to the closest point on an ellipse or rectangle."""
        snap_threshold = 0.2  # Adjust snapping sensitivity
        closest_point = (event.xdata, event.ydata)
        min_distance = float('inf')

        # Check snapping to ellipses and rectangles
        for shape in self.ax.patches:
            if isinstance(shape, Ellipse):
                points = self.get_ellipse_points(shape)
            elif isinstance(shape, Rectangle):
                points = self.get_rectangle_points(shape)
            else:
                continue

            for point in points:
                distance = ((event.xdata - point[0]) ** 2 + (event.ydata - point[1]) ** 2) ** 0.5
                if distance < min_distance and distance < snap_threshold:
                    min_distance = distance
                    closest_point = point

        # Update line to snap to the closest point
        x_data, y_data = line.get_data()
        if min_distance < snap_threshold:
            x_data[1], y_data[1] = closest_point

        line.set_data(x_data, y_data)
        self.canvas.draw()

    def get_ellipse_points(self, ellipse, num_points=100):
        """Get points around the perimeter of an ellipse."""
        angles = np.linspace(0, 2 * np.pi, num_points)
        center_x, center_y = ellipse.center
        width, height = ellipse.width / 2, ellipse.height / 2
        points = [(center_x + width * np.cos(a), center_y + height * np.sin(a)) for a in angles]
        return points

    def get_rectangle_points(self, rect):
        """Get the corner points of a rectangle."""
        x0, y0 = rect.xy
        x1, y1 = x0 + rect.get_width(), y0
        x2, y2 = x1, y0 + rect.get_height()
        x3, y3 = x0, y2
        return [(x0, y0), (x1, y1), (x2, y2), (x3, y3)]

    def draw_selection_rectangle(self):
        """Draw a selection rectangle around the selected shape."""
        if self.selection_rectangle and self.selection_rectangle in self.ax.patches:
            self.selection_rectangle.remove()
        if isinstance(self.selected_shape, Text):
            bbox = self.selected_shape.get_window_extent(self.canvas.get_renderer())
            self.selection_rectangle = Rectangle((bbox.x0, bbox.y0), bbox.width, bbox.height,
                                                 transform=None, edgecolor='blue', facecolor='none', linewidth=1)
        elif isinstance(self.selected_shape, Line2D):
            x_data, y_data = self.selected_shape.get_data()
            x_min, x_max = min(x_data), max(x_data)
            y_min, y_max = min(y_data), max(y_data)
            self.selection_rectangle = Rectangle((x_min, y_min), x_max - x_min, y_max - y_min,
                                                 edgecolor='blue', facecolor='none', linewidth=1)
        else:
            bbox = self.selected_shape.get_extents()
            self.selection_rectangle = Rectangle((bbox.x0, bbox.y0), bbox.width, bbox.height,
                                                 transform=None, edgecolor='blue', facecolor='none', linewidth=1)
        self.ax.add_patch(self.selection_rectangle)
        self.canvas.draw_idle()

    def update_selection_rectangle(self):
        """Update the position of the selection rectangle."""
        if self.selection_rectangle and self.selection_rectangle in self.ax.patches:
            self.selection_rectangle.remove()
        self.draw_selection_rectangle()

    def clear_canvas(self):
        """Clear the canvas of all shapes."""
        self.ax.clear()
        self.ax.set_xlim(0, 10)
        self.ax.set_ylim(0, 10)
        self.ax.axis('off')
        self.arrowheads.clear()
        self.canvas.draw()

    def add_arrowhead(self, line):
        """Add a solid triangle arrowhead to the end of a line, facing backwards."""
        x_data, y_data = line.get_data()
        dx = x_data[-1] - x_data[-2]
        dy = y_data[-1] - y_data[-2]
        angle = np.arctan2(dy, dx)
        arrow_length = 0.2
        arrow_width = 0.1

        if np.linalg.norm([dx, dy]) > arrow_length:
            # Calculate the new end point of the line
            end_x = x_data[-1] - arrow_length * np.cos(angle)
            end_y = y_data[-1] - arrow_length * np.sin(angle)

            # Define the vertices of the backward-facing solid triangle
            left_vertex = (x_data[-1] - arrow_length * np.cos(angle) - arrow_width * np.sin(angle), 
                           y_data[-1] - arrow_length * np.sin(angle) + arrow_width * np.cos(angle))
            right_vertex = (x_data[-1] - arrow_length * np.cos(angle) + arrow_width * np.sin(angle), 
                            y_data[-1] - arrow_length * np.sin(angle) - arrow_width * np.cos(angle))
            tip_vertex = (x_data[-1], y_data[-1])
            vertices = [left_vertex, right_vertex, tip_vertex]

            # Create the solid triangle arrowhead
            arrowhead = Polygon(vertices, closed=True, color=line.get_color())

            self.ax.add_patch(arrowhead)
            self.arrowheads.append(arrowhead)

            # Update the line data
            x_data[-1], y_data[-1] = end_x, end_y
            line.set_data(x_data, y_data)
            self.canvas.draw()

    def complete_cone(self, ellipse, cone_type):
        """Complete the drawing of a cone or upside-down cone."""
        cx, cy = ellipse.center
        width = ellipse.width / 2
        height = ellipse.height / 2

        # Increase the distance of the apex for more dramatic effect
        if cone_type == 'Cone':
            apex_y = cy + 2 * height  # Adjust this factor to change the height of the cone
        else:
            apex_y = cy - 2 * height  # Adjust for the upside-down cone

        apex = (cx, apex_y)
        left_base = (cx - width, cy)
        right_base = (cx + width, cy)

        # Draw the lines to form the cone
        line_left = Line2D([left_base[0], apex[0]], [left_base[1], apex[1]], color=ellipse.get_edgecolor(), linewidth=self.linewidth)
        line_right = Line2D([right_base[0], apex[0]], [right_base[1], apex[1]], color=ellipse.get_edgecolor(), linewidth=self.linewidth)

        self.ax.add_line(line_left)
        self.ax.add_line(line_right)
        self.history.append(line_left)
        self.history.append(line_right)
        self.canvas.draw()

    def generate_latex(self):
        """Generate LaTeX code for the drawn shapes."""
        latex_code = "\\begin{tikzpicture}\n"
        for shape in self.ax.patches:
            color = shape.get_edgecolor() if isinstance(shape, (Ellipse, Rectangle)) else shape.get_facecolor()
            color_name = self.color_var.get()
            if isinstance(shape, Ellipse):
                latex_code += f"\\draw [color={color_name}] ({shape.center[0]}, {shape.center[1]}) ellipse ({shape.width / 2} and {shape.height / 2});\n"
            elif isinstance(shape, Rectangle):
                latex_code += f"\\draw [color={color_name}] ({shape.xy[0]}, {shape.xy[1]}) rectangle ({shape.xy[0] + shape.get_width()}, {shape.xy[1] + shape.get_height()});\n"
            elif isinstance(shape, Polygon):
                vertices = shape.get_xy()
                latex_code += f"\\fill [color={color_name}] "
                latex_code += " -- ".join([f"({x}, {y})" for x, y in vertices])
                latex_code += " -- cycle;\n"
        for line in self.ax.lines:
            x_data, y_data = line.get_data()
            color_name = self.color_var.get()
            if isinstance(line, Line2D):
                if line in self.arrowheads:
                    latex_code += f"\\draw [->,color={color_name}] ({x_data[0]}, {y_data[0]}) -- ({x_data[1]}, {y_data[1]});\n"
                else:
                    latex_code += f"\\draw [color={color_name}] ({x_data[0]}, {y_data[0]}) -- ({x_data[1]}, {y_data[1]});\n"
        for text in self.ax.texts:
            color_name = self.color_var.get()
            latex_code += f"\\node at ({text.get_position()[0]}, {text.get_position()[1]}) [{color_name}] {{{text.get_text()}}};\n"
        latex_code += "\\end{tikzpicture}"

        self.show_latex_code(latex_code)

    def color_to_latex(self, color):
        """Map placeholder colors to LaTeX-compatible colors."""
        color_map = {
            '#ffffff': 'white',
            '#000000': 'black',
            '#ff0000': 'red',
            '#00ff00': 'green',
            '#0000ff': 'blue',
            '#00ffff': 'cyan',
            '#ff00ff': 'magenta',
            '#ffff00': 'yellow'
        }
        if isinstance(color, tuple):
            color = '#{:02x}{:02x}{:02x}'.format(int(color[0]*255), int(color[1]*255), int(color[2]*255))
        return color_map.get(color, 'black')

    def show_latex_code(self, latex_code):
        """Display the generated LaTeX code in a new window."""
        code_window = tk.Toplevel(self.root)
        code_window.title("Generated LaTeX Code")

        text_widget = tk.Text(code_window, wrap='word')
        text_widget.insert('1.0', latex_code)
        text_widget.config(state=tk.DISABLED)
        text_widget.pack(expand=True, fill=tk.BOTH)

        tk.Button(code_window, text="Close", command=code_window.destroy).pack(pady=5)

if __name__ == "__main__":
    root = tk.Tk()
    app = DrawToLatexApp(root)
    root.mainloop()
