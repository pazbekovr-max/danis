import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from datetime import datetime
import json
import os

class ExpenseTracker:
    def __init__(self, root):
        self.root = root
        self.root.title("Трекер расходов (GosPrompt AI)")
        self.root.geometry("800x600")

        # Файл для хранения данных
        self.data_file = "expenses.json"
        self.expenses = []
        self.load_data()

        # --- Интерфейс ---
        
        # 1. Форма ввода
        input_frame = ttk.LabelFrame(root, text="Добавить расход", padding=10)
        input_frame.pack(fill="x", padx=10, pady=5)

        # Сумма
        ttk.Label(input_frame, text="Сумма:").grid(row=0, column=0, sticky="w")
        self.amount_var = tk.StringVar()
        self.amount_entry = ttk.Entry(input_frame, textvariable=self.amount_var, width=15)
        self.amount_entry.grid(row=0, column=1, padx=5)

        # Категория
        ttk.Label(input_frame, text="Категория:").grid(row=0, column=2, sticky="w")
        self.category_var = tk.StringVar()
        categories = ["Еда", "Транспорт", "Развлечения", "Жилье", "Здоровье", "Другое"]
        self.category_combo = ttk.Combobox(input_frame, textvariable=self.category_var, values=categories, width=15, state="readonly")
        self.category_combo.grid(row=0, column=3, padx=5)
        self.category_combo.current(0)

        # Дата
        ttk.Label(input_frame, text="Дата (ДД.ММ.ГГГГ):").grid(row=0, column=4, sticky="w")
        self.date_var = tk.StringVar()
        self.date_entry = ttk.Entry(input_frame, textvariable=self.date_var, width=15)
        self.date_entry.insert(0, datetime.now().strftime("%d.%m.%Y"))
        self.date_entry.grid(row=0, column=5, padx=5)

        # Кнопка добавления
        ttk.Button(input_frame, text="Добавить расход", command=self.add_expense).grid(row=0, column=6, padx=10)

        # 2. Фильтры и Подсчет
        filter_frame = ttk.LabelFrame(root, text="Фильтры и Статистика", padding=10)
        filter_frame.pack(fill="x", padx=10, pady=5)

        # Фильтр по категории
        ttk.Label(filter_frame, text="Фильтр по категории:").grid(row=0, column=0, sticky="w")
        self.filter_category_var = tk.StringVar(value="Все")
        filter_combo = ttk.Combobox(filter_frame, textvariable=self.filter_category_var, values=["Все"] + categories, width=15, state="readonly")
        filter_combo.grid(row=0, column=1, padx=5)
        filter_combo.bind("<<ComboboxSelected>>", self.apply_filters)

        # Фильтр по дате (от и до)
        ttk.Label(filter_frame, text="С:").grid(row=0, column=2, sticky="w")
        self.filter_date_start = ttk.Entry(filter_frame, width=12)
        self.filter_date_start.grid(row=0, column=3, padx=2)
        
        ttk.Label(filter_frame, text="По:").grid(row=0, column=4, sticky="w")
        self.filter_date_end = ttk.Entry(filter_frame, width=12)
        self.filter_date_end.grid(row=0, column=5, padx=2)

        ttk.Button(filter_frame, text="Применить фильтр", command=self.apply_filters).grid(row=0, column=6, padx=10)
        ttk.Button(filter_frame, text="Сбросить", command=self.reset_filters).grid(row=0, column=7, padx=5)

        # Итоговая сумма
        self.total_label = ttk.Label(filter_frame, text="Итого: 0.00 руб.", font=("Arial", 12, "bold"))
        self.total_label.grid(row=0, column=8, padx=20)

        # Кнопки управления файлом
        file_frame = ttk.Frame(root)
        file_frame.pack(fill="x", padx=10, pady=5)
        ttk.Button(file_frame, text="Сохранить в JSON", command=self.save_data).pack(side="left", padx=5)
        ttk.Button(file_frame, text="Загрузить из JSON", command=self.load_data_gui).pack(side="left", padx=5)

        # 3. Таблица (Treeview)
        columns = ("id", "date", "category", "amount")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=15)
        
        self.tree.heading("id", text="ID")
        self.tree.heading("date", text="Дата")
        self.tree.heading("category", text="Категория")
        self.tree.heading("amount", text="Сумма")

        self.tree.column("id", width=50)
        self.tree.column("date", width=100)
        self.tree.column("category", width=150)
        self.tree.column("amount", width=100)

        # Скроллбар
        scrollbar = ttk.Scrollbar(root, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)

        self.tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        scrollbar.pack(side="right", fill="y")

        # Загрузка данных при старте
        self.refresh_table()

    def validate_input(self):
        """Проверка корректности ввода"""
        try:
            amount = float(self.amount_var.get())
            if amount <= 0:
                messagebox.showerror("Ошибка", "Сумма должна быть положительным числом.")
                return False
            
            date_str = self.date_var.get()
            datetime.strptime(date_str, "%d.%m.%Y")
            return True
        except ValueError:
            messagebox.showerror("Ошибка", "Неверный формат данных. Проверьте сумму и дату (ДД.ММ.ГГГГ).")
            return False

    def add_expense(self):
        if not self.validate_input():
            return

        amount = float(self.amount_var.get())
        category = self.category_var.get()
        date_str = self.date_var.get()

        new_expense = {
            "id": len(self.expenses) + 1,
            "date": date_str,
            "category": category,
            "amount": amount
        }

        self.expenses.append(new_expense)
        self.refresh_table()
        self.save_data() # Автосохранение
        
        # Очистка полей
        self.amount_var.set("")
        self.amount_entry.focus()

    def refresh_table(self, filtered_data=None):
        # Очистка таблицы
        for row in self.tree.get_children():
            self.tree.delete(row)

        data_to_show = filtered_data if filtered_data is not None else self.expenses

        total = 0.0
        for item in data_to_show:
            self.tree.insert("", "end", values=(item["id"], item["date"], item["category"], f"{item['amount']:.2f}"))
            total += item["amount"]

        self.total_label.config(text=f"Итого: {total:.2f} руб.")

    def apply_filters(self, event=None):
        category_filter = self.filter_category_var.get()
        start_date = self.filter_date_start.get()
        end_date = self.filter_date_end.get()

        filtered = []
        for item in self.expenses:
            # Фильтр по категории
            if category_filter != "Все" and item["category"] != category_filter:
                continue
            
            # Фильтр по дате
            if start_date:
                try:
                    s_dt = datetime.strptime(start_date, "%d.%m.%Y")
                    i_dt = datetime.strptime(item["date"], "%d.%m.%Y")
                    if i_dt < s_dt:
                        continue
                except ValueError:
                    pass # Игнорируем некорректную дату фильтра

            if end_date:
                try:
                    e_dt = datetime.strptime(end_date, "%d.%m.%Y")
                    i_dt = datetime.strptime(item["date"], "%d.%m.%Y")
                    if i_dt > e_dt:
                        continue
                except ValueError:
                    pass

            filtered.append(item)

        self.refresh_table(filtered)

    def reset_filters(self):
        self.filter_category_var.set("Все")
        self.filter_date_start.delete(0, tk.END)
        self.filter_date_end.delete(0, tk.END)
        self.refresh_table()

    def save_data(self):
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.expenses, f, ensure_ascii=False, indent=4)
            messagebox.showinfo("Успех", "Данные успешно сохранены в expenses.json")
        except Exception as e:
            messagebox.showerror("Ошибка", f"Не удалось сохранить файл: {e}")

    def load_data_gui(self):
        file_path = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json")])
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    self.expenses = json.load(f)
                self.refresh_table()
                messagebox.showinfo("Успех", "Данные загружены!")
            except Exception as e:
                messagebox.showerror("Ошибка", f"Ошибка чтения файла: {e}")

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.expenses = json.load(f)
            except json.JSONDecodeError:
                self.expenses = []
        else:
            self.expenses = []

if __name__ == "__main__":
    root = tk.Tk()
    app = ExpenseTracker(root)
    root.mainloop()
