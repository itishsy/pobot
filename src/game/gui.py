import tkinter as tk
from tkinter import messagebox
import math
import logging

from src.train.act import GameLogic, Action

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class PokerGUI:
    def __init__(self, root):
        logger.info("初始化PokerGUI")
        self.root = root
        self.root.title("AIPokerTrainer")
        self.root.geometry("900x700")
        self.root.minsize(900, 700)
        # 添加关闭窗口时的回调
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

        # 定义颜色主题 - 低调风格
        self.colors = {
            'bg': '#f5f5f5',          # 浅灰色背景
            'table': '#0f4d2d',       # 深绿色桌子（低调）
            'frame': '#5d6d7e',       # 深灰蓝色框架
            'text': '#ffffff',        # 白色文字
            'highlight': '#d4ac0d',   # 金色高亮（低调）
            'pot': '#8e44ad',         # 深紫色底池显示
            'button': '#2c3e50',      # 深蓝灰色按钮
            'button_hover': '#3498db', # 蓝色按钮悬停
            'active_border': '#e74c3c', # 深红色活跃玩家边框
            'inactive_frame': '#555555' # 深灰色已弃牌玩家框架
        }
        logger.info("颜色主题已设置")

        # 设置背景色
        self.root.configure(bg=self.colors['bg'])
        logger.info(f"背景色已设置为: {self.colors['bg']}")

        # 创建游戏逻辑实例
        self.game = GameLogic()

        # 创建UI组件
        self.create_widgets()

        # 初始化游戏
        self.start_new_game()

    def set_background_color(self, color):
        """设置窗体背景色"""
        self.colors['bg'] = color
        self.root.configure(bg=color)
        # 更新相关UI元素的背景色
        self.bottom_frame.configure(bg=color)
        self.action_frame.configure(bg=color)
        self.main_frame.configure(bg=color)
        self.result_frame.configure(bg=color)

    def create_widgets(self):
        # 创建主框架，用于放置桌子和结果区域
        self.main_frame = tk.Frame(self.root, bg=self.colors['bg']) 
        self.main_frame.pack(pady=5, fill=tk.BOTH, expand=True)

        # 配置主框架的行和列权重
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)

        # 桌子区域
        self.table_frame = tk.Frame(self.main_frame, bg=self.colors['table'], width=620, height=480,
                                    highlightthickness=2, highlightbackground=self.colors['frame'])
        self.table_frame.grid(row=0, column=0, padx=10, pady=10, sticky='nsew')
        self.table_frame.pack_propagate(False)

        # 玩家座位区域 - 调整布局，确保所有玩家框架显示在桌子区域内
        logger.info("创建玩家框架")
        self.player_frames = []
        table_center_x, table_center_y = 300, 260
        radius = 200  # 减小半径以确保所有玩家框架显示在620宽的桌子内
        # 6个玩家均匀分布在桌子周围
        angles = [
            2 * math.pi / 3,     # 120度 (左上)
            math.pi / 3,         # 60度 (中上)
            0,                   # 0度 (右上)
            -math.pi / 3,        # -60度 (右下)
            -2 * math.pi / 3,    # -120度 (左下)
            math.pi              # 180度 (正左)
        ]

        for i in range(6):
            angle = angles[i]
            x = table_center_x + radius * math.cos(angle) - 40
            y = table_center_y - radius * math.sin(angle) - 30
            frame = tk.Frame(self.table_frame, bg=self.colors['frame'], width=120, height=100,
                             relief=tk.RAISED, bd=2, highlightthickness=2, highlightbackground=self.colors['table'])
            frame.place(x=x, y=y)
            frame.pack_propagate(False)
            self.player_frames.append(frame)
            logger.info(f"创建玩家 {i+1} 框架，位置: x={x}, y={y}")

            # 玩家名称
            name_label = tk.Label(frame, text=self.game.players[i].name, bg=self.colors['frame'], fg=self.colors['text'],
                                  font=('SimHei', 10, 'bold'))
            name_label.pack(pady=2)

            # 玩家筹码
            chips_label = tk.Label(frame, text=f"筹码: {self.game.players[i].chips}", bg=self.colors['frame'], fg=self.colors['text'],
                                   font=('SimHei', 8))
            chips_label.pack()
            setattr(self, f"player_{i}_chips_label", chips_label)

            # 玩家状态标识
            status_label = tk.Label(frame, text="", bg=self.colors['frame'], fg=self.colors['pot'],
                                    font=('SimHei', 8, 'bold'))
            status_label.pack()
            setattr(self, f"player_{i}_status_label", status_label)

            # 玩家手牌区域
            hand_frame = tk.Frame(frame, bg="#34495e")
            hand_frame.pack(pady=2)
            setattr(self, f"player_{i}_hand_frame", hand_frame)

        # 底池显示区域
        self.pot_display_frame = tk.Frame(self.table_frame, bg=self.colors['table'], width=120, height=40,
                                         relief=tk.RAISED, bd=3, highlightthickness=2, highlightbackground=self.colors['pot'])
        self.pot_display_frame.place(x=260, y=180)
        self.pot_display_frame.pack_propagate(False)
        self.pot_display_label = tk.Label(self.pot_display_frame, text=f"底池: {self.game.pot}", bg=self.colors['table'], fg=self.colors['pot'],
                                          font=('SimHei', 18, 'bold'))
        self.pot_display_label.pack(expand=True)

        # 公共牌区域 - 调整位置避免挡住玩家
        self.community_frame = tk.Frame(self.table_frame, bg=self.colors['table'], width=270, height=120,
                                        relief=tk.RAISED, bd=2, highlightthickness=2, highlightbackground=self.colors['frame'])
        self.community_frame.place(x=185, y=220)  # 向上移动避免挡住下方玩家
        self.community_frame.pack_propagate(False)

        # 确保所有玩家框架都在可见区域内
        for i, frame in enumerate(self.player_frames):
            x = frame.winfo_x()
            y = frame.winfo_y()
            width = frame.winfo_width()
            height = frame.winfo_height()

            # 确保框架不超出桌子区域
            if x < 0:
                frame.place(x=0, y=y)
            elif x + width > 600:
                frame.place(x=600 - width, y=y)

            if y < 0:
                frame.place(x=x, y=0)
            elif y + height > 480:
                frame.place(x=x, y=480 - height)

        # 结果显示区域 - 移到右侧
        self.result_frame = tk.Frame(self.main_frame, bg=self.colors['bg'], width=220, height=480)
        self.result_frame.grid(row=0, column=1, padx=5, pady=0, sticky='nsew')
        self.result_frame.pack_propagate(False)

        # 设置列权重，让结果区域可以适当扩展
        self.main_frame.grid_columnconfigure(0, weight=3)
        self.main_frame.grid_columnconfigure(1, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

        # 结果文本框
        self.result_text = tk.Text(self.result_frame, height=20, width=30, bg=self.colors['frame'], fg=self.colors['text'],
                                  font=('SimHei', 12), relief=tk.RAISED, bd=2)
        self.result_text.pack(pady=10, fill=tk.BOTH, expand=True)

        # 创建底部框架，包含游戏信息和操作按钮
        self.bottom_frame = tk.Frame(self.root, bg=self.colors['bg'])
        self.bottom_frame.pack(side=tk.BOTTOM, pady=0, fill=tk.X)

        # 操作按钮区域
        self.action_frame = tk.Frame(self.bottom_frame, bg=self.colors['bg'])
        self.action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)

        # 按钮容器，用于居中按钮
        self.button_container = tk.Frame(self.action_frame, bg=self.colors['bg'])
        self.button_container.pack(side=tk.TOP)

        # 自定义按钮样式
        def create_button(text, command):
            button = tk.Button(self.button_container, text=text, command=command, width=12, height=2,
                              bg=self.colors['button'], fg=self.colors['text'], font=('SimHei', 12, 'bold'),
                              relief=tk.RAISED, bd=3, activebackground=self.colors['button_hover'])
            button.pack(side=tk.LEFT, padx=8, pady=5)
            return button

        self.fold_button = create_button("弃牌", lambda: self.player_action(Action.FOLD))
        self.check_button = create_button("过牌", lambda: self.player_action(Action.CHECK))
        self.call_button = create_button("跟注", lambda: self.player_action(Action.CALL))
        # 加注按钮和额度输入
        self.raise_frame = tk.Frame(self.button_container, bg=self.colors['bg'])        
        self.raise_frame.pack(side=tk.LEFT, padx=8, pady=5)
        
        self.raise_entry = tk.Entry(self.raise_frame, width=10, font=('SimHei', 12))
        self.raise_entry.pack(side=tk.LEFT, padx=2)
        self.raise_entry.insert(0, "2")  # 默认加注金额
        
        self.raise_button = tk.Button(self.raise_frame, text="加注", command=self.raise_with_amount, width=8, height=2,
                              bg=self.colors['button'], fg=self.colors['text'], font=('SimHei', 12, 'bold'),
                              relief=tk.RAISED, bd=3, activebackground=self.colors['button_hover'])
        self.raise_button.pack(side=tk.LEFT)
        

    def start_new_game(self):
        logger.info("开始新游戏")
        # 重置游戏状态
        self.game.start_new_game()

        # 清除公共牌显示
        self.display_community_cards()

        # 更新UI显示
        self.update_player_status()
        self.update_chips_display()
        self.update_pot_display()

        # 更新结果显示
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(tk.END, "新游戏开始！\n")
        # 设置庄家、小盲注和大盲注文本颜色
        self.result_text.tag_config("dealer", foreground="#ffd700")  # 金色
        self.result_text.tag_config("small_blind", foreground="#add8e6")  # 浅蓝色
        self.result_text.tag_config("big_blind", foreground="#ff6347")  # 鲜红色

        self.result_text.insert(tk.END, "庄家: ")
        self.result_text.insert(tk.END, f"{self.game.players[self.game.dealer_index].name}\n", "dealer")
        self.result_text.insert(tk.END, "小盲注: ")
        self.result_text.insert(tk.END, f"{self.game.players[self.game.small_blind_index].name} (1)\n", "small_blind")
        self.result_text.insert(tk.END, "大盲注: ")
        self.result_text.insert(tk.END, f"{self.game.players[self.game.big_blind_index].name} (2)\n", "big_blind")

        # 发牌给玩家
        self.game.deal_hole_cards()
        for i, player in enumerate(self.game.players):
            for card in player.hand:
                self.display_player_card(i, card)

        # 启用操作按钮
        self.enable_action_buttons()
        logger.info("操作按钮已启用")

    def display_player_card(self, player_index, card):
        frame = getattr(self, f"player_{player_index}_hand_frame")
        for widget in frame.winfo_children():
            widget.destroy()

        for c in self.game.players[player_index].hand:
            card_label = tk.Label(frame, text=f"{c[0]}{c[1]}", font=('SimHei', 10, 'bold'), width=5, height=1,
                                  bg="white" if c[1] in ['♠', '♣'] else "#fff9c4",
                                  fg="black" if c[1] in ['♠', '♣'] else "#d32f2f",
                                  relief=tk.RAISED, bd=1)
            card_label.pack(side=tk.LEFT, padx=2)

    def display_community_cards(self):
        for widget in self.community_frame.winfo_children():
            widget.destroy()

        for card in self.game.community_cards:
            card_label = tk.Label(self.community_frame, text=f"{card[0]}{card[1]}", font=('SimHei', 12, 'bold'), width=5, height=4,
                                  bg="white" if card[1] in ['♠', '♣'] else "#fff9c4",
                                  fg="black" if card[1] in ['♠', '♣'] else "#d32f2f",
                                  relief=tk.RAISED, bd=2)
            card_label.pack(side=tk.LEFT, padx=1, pady=10)  # 减少边距，让更多牌能显示

    def update_player_status(self):
        for i, player in enumerate(self.game.players):
            status = []
            if player.is_dealer:
                status.append("庄家")
            if player.is_small_blind:
                status.append("小盲")
            if player.is_big_blind:
                status.append("大盲")
            if not player.is_active:
                status.append("已弃牌")

            status_label = getattr(self, f"player_{i}_status_label")
            status_label.config(text=", ".join(status))

            # 根据玩家状态设置标签颜色
            if player.is_dealer:
                status_label.config(fg="#ffd700")  # 金色
            elif player.is_small_blind:
                status_label.config(fg="#add8e6")  # 浅蓝色
            elif player.is_big_blind:
                status_label.config(fg="#ff6347")  # 鲜红色
            else:
                status_label.config(fg=self.colors['text'])  # 默认文本颜色

            # 更新玩家状态显示
            frame = self.player_frames[i]
            if player.is_active:
                # 活跃玩家：红色边框
                frame.config(bg=self.colors['frame'], highlightbackground=self.colors['active_border'], highlightthickness=3)
                # 当前玩家额外高亮
                if i == self.game.current_player_index:
                    frame.config(bg=self.colors['highlight'])
                    # 添加闪烁效果
                    self.root.after(0, self.blink_player_frame, frame, 0)
            else:
                # 已弃牌玩家：灰色效果
                frame.config(bg=self.colors['inactive_frame'], highlightbackground=self.colors['table'], highlightthickness=1)
                # 灰掉玩家名称和筹码标签
                name_label = frame.winfo_children()[0]
                chips_label = frame.winfo_children()[1]
                name_label.config(fg='#aaaaaa')
                chips_label.config(fg='#aaaaaa')

    def blink_player_frame(self, frame, count):
        # 简单的闪烁效果，闪烁3次
        if count < 4:
            current_bg = frame.cget('bg')
            new_bg = self.colors['frame'] if current_bg == self.colors['highlight'] else self.colors['highlight']
            frame.config(bg=new_bg)
            self.root.after(300, self.blink_player_frame, frame, count + 1)

    def update_chips_display(self):
        for i, player in enumerate(self.game.players):
            chips_label = getattr(self, f"player_{i}_chips_label")
            chips_label.config(text=f"筹码: {player.chips}")
        self.root.update_idletasks()  # 强制刷新UI，确保筹码更新立即显示

    def update_pot_display(self):
        self.pot_display_label.config(text=f"底池: {self.game.pot}")

    def enable_action_buttons(self):
        """启用所有操作按钮"""
        logger.info("启用所有操作按钮")
        self.fold_button.config(state=tk.NORMAL)
        logger.info("启用弃牌按钮")
        self.check_button.config(state=tk.NORMAL)
        logger.info("启用过牌按钮")
        self.call_button.config(state=tk.NORMAL)
        logger.info("启用跟注按钮")
        self.raise_button.config(state=tk.NORMAL)
        logger.info("启用加注按钮")

    def disable_action_buttons(self):
        self.fold_button.config(state=tk.DISABLED)
        self.check_button.config(state=tk.DISABLED)
        self.call_button.config(state=tk.DISABLED)
        self.raise_button.config(state=tk.DISABLED)

    def player_action(self, action, raise_amount=None):
        result = self.game.player_action(action, raise_amount)
        if result['success']:
            self.result_text.insert(tk.END, result['message'])
            self.update_chips_display()
            self.update_pot_display()
            self.move_to_next_player()
        else:
            messagebox.showerror("错误", result['message'])
            
    def raise_with_amount(self):
        try:
            amount = int(self.raise_entry.get())
            if amount <= 0:
                messagebox.showerror("错误", "加注金额必须大于0")
                return
            self.player_action(Action.RAISE, amount)
        except ValueError:
            messagebox.showerror("错误", "请输入有效的加注金额")

    def move_to_next_player(self):
        # 检查是否所有玩家都已行动
        next_player_info = self.game.move_to_next_player()

        if next_player_info['end_hand']:
            self.end_hand(next_player_info['winner'])
            return
        elif next_player_info['end_round']:
            self.end_betting_round()
        else:
            # 直接更新玩家状态，不再更新当前玩家标签
            self.update_player_status()

    def end_betting_round(self):
        self.result_text.insert(tk.END, "下注轮结束\n")
        round_info = self.game.end_betting_round()

        if round_info['showdown']:
            self.result_text.insert(tk.END, "摊牌！\n")
            winner_info = self.game.determine_winner()
            self.result_text.insert(tk.END, winner_info['message'])
            self.update_chips_display()
            self.root.update()  # 强制立即更新整个UI
            self.root.after(3000, self.start_new_game)
            return
        else:
            # 发公共牌
            if round_info['community_cards_added']:
                self.display_community_cards()

            self.update_player_status()

    def end_hand(self, winner_info):
        # 直接使用传入的winner_info，它已经包含了获胜者信息
        self.result_text.insert(tk.END, winner_info['message'])
        self.update_chips_display()
        self.root.update()  # 强制立即更新整个UI
        # 从game对象中获取实际的获胜者
        active_players = [p for p in self.game.players if p.is_active]
        if len(active_players) == 1:
            actual_winner = active_players[0]
        else:
            actual_winner = active_players[0]
        logger.info(f"游戏结束，获胜者: {actual_winner.name}")
        self.root.after(3000, self.start_new_game)

    def on_closing(self):
        logger.info("窗口关闭。")
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = PokerGUI(root)
    root.mainloop()