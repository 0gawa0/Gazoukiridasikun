import tkinter as tk
import cv2
import os
from PIL import Image, ImageTk
from tkinter import filedialog
from tkinter import messagebox

class Application(tk.Frame):
    def __init__(self, master=None, title="画像切り出しくん", width=900, height=600):
        super().__init__(master)
        master.geometry(f"{width}x{height}")
        master.title(title)
        self.pack()
        # 読み込んだ画像のサイズ
        self.width = width
        self.height = height

        self.resize_edge = 0
        self.resize_radio = 0
        # マウスの座標
        self.mouse_x = 0
        self.mouse_y = 0
        self.mouse_start = True
        self.mouse_shape = None
        # 画像を保存しておくための変数
        self.img = None
        self.original_img = None
        # 画像の切り取りサイズ（一辺の長さ）
        self.cut_size = 32
        # 前に選択された領域のタグ名とインデックス
        self.preselect_tag = None
        self.presetect_index = 0
        self.preselect_text_tag = None

        self.select_box_num = 0
        self.select_boxs = []
        self.select_box_tags = []
        self.select_text_tags = []

        self.create_widgets()
    
    def create_widgets(self):
        # 画像表示用フレーム
        self.left_frame = tk.Frame(self.master, bg="white")
        self.left_frame.place(relx=0.01, rely=0.01, relwidth=0.6, relheight=0.98)

        self.canvas = tk.Canvas(self.left_frame, bg="gray")
        self.canvas.place(relwidth=1, relheight=1)
        self.canvas.bind("<ButtonPress-1>", self.mouse_click)
        self.canvas.bind("<Motion>", self.mouse_move)

        # ボタン配置用フレーム
        self.right_frame = tk.Frame(self.master)
        self.right_frame.place(relx=0.62, rely=0.01, relwidth=0.365, relheight=0.98)

        self.open_btn = tk.Button(self.right_frame, text="open", font=("MSゴシック", "20"), command=self.load_img)
        self.open_btn.pack()

        strvar1 = tk.StringVar(value="./img/output")
        strvar2 = tk.StringVar(value="output")
        self.list_var = tk.StringVar(value=[])
        # クリックした時の座標を表示
        self.show_coordinate_label = tk.Label(self.right_frame)
        self.show_coordinate_label.pack()
        # 選択した領域の一覧を表示する
        self.list_label = tk.Label(self.right_frame, text="選択された領域")
        self.list_label.pack()
        self.explain_label = tk.Label(self.right_frame, text="(選択した状態でDを押すと削除、Cを押すと選択解除)")
        self.explain_label.pack()
        self.list_select = tk.Listbox(self.right_frame, width=30, height=20, list=self.list_var)
        self.list_select.pack()
        self.list_select.bind("<<ListboxSelect>>", self.selected_box)
        self.list_select.bind("<KeyPress-c>", self.select_chancel)
        self.list_select.bind("<KeyPress-d>", self.select_delete)

        self.scrollbar = tk.Scrollbar(self.right_frame, orient="vertical", command=self.list_select.yview)
        self.list_select["yscrollcommand"] = self.scrollbar.set

        self.file_path_label = tk.Label(self.right_frame, text="保存先パス（末尾に/はつけない）")
        self.file_path_label.pack()
        self.filepath_textarea = tk.Entry(self.right_frame, textvariable=strvar1)
        self.filepath_textarea.pack()
        self.file_name_label = tk.Label(self.right_frame, text="ファイル名")
        self.file_name_label.pack()
        self.filename_textarea = tk.Entry(self.right_frame, textvariable=strvar2)
        self.filename_textarea.pack()
        self.save_btn = tk.Button(self.right_frame, text="save", font=("MSゴシック", "20"), command=self.save_img)
        self.save_btn.pack()
        

    def load_img(self):
        self.delete_shape()
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()

        # 確認用
        print("canvas width:" + str(canvas_width))
        print("canvas height:" + str(canvas_height))
        # 画像ファイルの読み込み
        filepath = filedialog.askopenfilename(title="画像ファイルを選択")
        img = cv2.imread(filepath)
        self.original_img = img
        # 確認用
        print(img.shape)
        original_img_height, original_img_width, channels = img.shape[:3]
        self.width = original_img_width
        self.height = original_img_height
        # 読み込んだ画像のうち長さが短い辺を格納する
        self.resize_edge = original_img_height if original_img_height>original_img_width else original_img_width
        # 表示するキャンバスに合わせてリサイズするための値（長さがより長い辺に合わせる）
        self.resize_radio = canvas_height / self.resize_edge if original_img_height>original_img_width else canvas_width / self.resize_edge
        img = cv2.resize(img, (int(original_img_width*self.resize_radio), int(original_img_height*self.resize_radio)))
        # リサイズ後の画像サイズを表示
        a, b, c = img.shape[:3]
        print(f'{a}, {b}, {self.resize_radio}')
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        self.img = ImageTk.PhotoImage(img_pil)

        self.update()

        self.canvas.create_image(int(canvas_width/2), int(canvas_height/2), image=self.img)

    def mouse_click(self, event):
        draw_flag = True
        tag = "rect" + str(self.select_box_num)
        text_tag = "text" + str(self.select_box_num)
        h = self.cut_size * self.resize_radio / 2
        if len(self.select_boxs) > 0:
            box_left = event.x - h
            box_right = event.x + h
            box_bottom = event.y - h
            box_top = event.y + h
            for i in self.select_boxs:
                existing_x = i.get_x()
                existing_y = i.get_y()
                if box_left > existing_x[1]:
                    continue
                if box_right < existing_x[0]:
                    continue
                if box_bottom > existing_y[2]:
                    continue
                if box_top < existing_y[0]:
                    continue
                draw_flag = False
                break

        # クリックして描画する図形とすでにある図形の重なりがなければ新しく描画する
        if draw_flag:       
            id = self.canvas.create_rectangle(event.x-h, event.y-h, event.x+h, event.y+h,outline="red", tag=tag)
            text_id = self.canvas.create_text(event.x+h*3/4, event.y+h*3/4, text=str(self.select_box_num), tag=text_tag, fill="red", font=("MSゴシック", "10"))
            self.show_coordinate_label["text"] = f'x:{event.x}, y:{event.y}'
            self.select_box_tags.append(tag)
            self.list_var.set(self.select_box_tags)
            self.select_text_tags.append(text_tag)

            self.select_box_num += 1
            box_info = SelectBoxInfo(id, event.x, event.y, tag, h, text_id)
            self.select_boxs.append(box_info)

        self.mouse_x = event.x
        self.mouse_y = event.y
    
    # カーソルに合わせて描画する図形を追跡させる
    def mouse_move(self, event):
        h = self.cut_size * self.resize_radio / 2
        if self.mouse_shape:
            self.canvas.coords("mouse", event.x-h, event.y-h, event.x+h, event.y+h)
        if self.mouse_start:
            self.mouse_shape = "mouse"
            self.canvas.create_rectangle(event.x-h, event.y-h, event.x+h, event.y+h,outline="blue", tag="mouse")
            self.mouse_start = False
        if event.x <= 0 or event.x >= self.canvas.winfo_width() or event.y <= 0 or event.y >= self.canvas.winfo_height():
            self.canvas.delete("mouse")
            self.mouse_start = True
            self.mouse_shape = None

    # 選択した領域を削除する
    def delete_shape(self):
        if len(self.select_boxs) > 0:
            cnt = 0
            for i in self.select_boxs:
                self.canvas.delete(i)
                self.list_select.delete(cnt)
                cnt += 1

        self.list_var.set("")
        self.select_boxs = []
        self.select_box_tags = []
        self.select_box_num = 0
        self.select_text_tags = []
        self.mouse_start = True
        self.mouse_shape = None
        self.preselect_tag = None
        self.presetect_index = 0
        self.mouse_x = 0
        self.mouse_y = 0
    
    def save_img(self):
        if len(self.select_boxs) > 0:
            num = 0
            for i in self.select_boxs:
                box_x_arr = i.get_x()
                box_y_arr = i.get_y()
                original_x = int(box_x_arr[3] / self.resize_radio)
                original_y = int((box_y_arr[3] - (self.canvas.winfo_height() - self.height*self.resize_radio)/2) / self.resize_radio)
                timg = self.original_img[original_y-self.cut_size:original_y, original_x-self.cut_size:original_x]
                # 確認用
                print(timg.shape)
                if not(os.path.isdir(self.filepath_textarea.get())):
                    os.makedirs(self.filepath_textarea.get())
                    break

                save = cv2.imwrite(f'{self.filepath_textarea.get()}/{self.filename_textarea.get()}{num}.jpg', timg)
                if not(save):
                    messagebox.showerror("保存時のエラー", "ファイルの保存に失敗しました")
                    break
                num += 1
            
            if num == self.select_box_num:
                messagebox.showinfo("ポップアップ", "画像ファイルが出力されました")
    
    def selected_box(self, event):
        selected_index = self.list_select.curselection()
        selected_tag = self.list_select.get(selected_index)
        selected_text = self.select_text_tags[selected_index[0]]

        if self.preselect_tag:
            # 前に選択した領域の情報を取得し、その領域の図形の色を元に戻す
            self.canvas.itemconfig(self.preselect_tag, outline="red")
            self.canvas.itemconfig(self.preselect_text_tag, fill="red")

        self.preselect_tag = selected_tag
        self.presetect_index = selected_index
        self.preselect_text_tag = selected_text
        self.canvas.itemconfig(selected_tag, outline="yellow")
        self.canvas.itemconfig(selected_text, fill="yellow")
    
    # 選択したボックスを解除する処理
    def select_chancel(self, event):
        self.canvas.itemconfig(self.preselect_tag, outline="red")
        self.canvas.itemconfig(self.preselect_text_tag, fill="red")
        self.preselect_tag = None
        self.preselect_text_tag = None
        self.presetect_index = 0
    
    # 選択したボックスを削除する処理
    def select_delete(self, event):
        self.select_boxs.pop(self.presetect_index[0])
        self.select_box_tags.pop(self.presetect_index[0])
        self.select_text_tags.pop(self.presetect_index[0])
        self.canvas.delete(self.preselect_tag)
        self.canvas.delete(self.preselect_text_tag)

        for i in range(len(self.select_boxs)):
            print(i)
            if i >= self.presetect_index[0]:
                box_info = self.select_boxs[i]
                new_tag = f'rect{i}'
                new_text_tag = f'text{i}'
                self.canvas.itemconfig(box_info.get_id(), tag=new_tag)
                self.canvas.itemconfig(box_info.get_text_id(), tag=new_text_tag, text=str(i))
                box_info.set_tag(new_tag)
                self.select_box_tags[i] = new_tag
                self.select_text_tags[i] = new_text_tag
        
        self.list_var.set(self.select_box_tags)
        self.select_box_num -= 1



class SelectBoxInfo:
    def __init__(self, id, x, y, tag, width, text_id) -> None:
        a = [-1, 1, -1, 1]
        b = [-1, -1, 1, 1]
        self.box_x = []
        self.box_y = []
        for i in range(4):
            self.box_x.append(x+width*a[i])
            self.box_y.append(y+width*b[i])
        self.tag = tag
        self.id = id
        self.text_id = text_id
    
    def get_x(self):
        return self.box_x
    
    def get_y(self):
        return self.box_y
    
    def get_tag(self):
        return self.tag
    
    def get_id(self):
        return self.id
    
    def get_text_id(self):
        return self.text_id
    
    def set_tag(self, tag):
        self.tag = tag

if __name__ == '__main__':
    root = tk.Tk()
    app = Application(master=root)
    app.mainloop()