import pygame,sys,random,time
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
ZOOM = 10
START_ADDR = 0x200
CLOCK_SPEED = 700
TIMER_SPEED = 60
_FONTSET = [0xF0, 0x90, 0x90, 0x90, 0xF0,  # 0
            0x20, 0x60, 0x20, 0x20, 0x70,  # 1
            0xF0, 0x10, 0xF0, 0x80, 0xF0,  # 2
            0xF0, 0x10, 0xF0, 0x10, 0xF0,  # 3
            0x90, 0x90, 0xF0, 0x10, 0x10,  # 4
            0xF0, 0x80, 0xF0, 0x10, 0xF0,  # 5
            0xF0, 0x80, 0xF0, 0x90, 0xF0,  # 6
            0xF0, 0x10, 0x20, 0x40, 0x40,  # 7
            0xF0, 0x90, 0xF0, 0x90, 0xF0,  # 8
            0xF0, 0x90, 0xF0, 0x10, 0xF0,  # 9
            0xF0, 0x90, 0xF0, 0x90, 0x90,  # A
            0xE0, 0x90, 0xE0, 0x90, 0xE0,  # B
            0xF0, 0x80, 0x80, 0x80, 0xF0,  # C
            0xE0, 0x90, 0x90, 0x90, 0xE0,  # D
            0xF0, 0x80, 0xF0, 0x80, 0xF0,  # E
            0xF0, 0x80, 0xF0, 0x80, 0x80]  # F
def load_file(filepath:str):
    try:
        data = []
        with open(filepath,'rb') as f:
            file_bytes = f.read()
            for i in range(len(file_bytes)):
                data.append(file_bytes[i])
    except Exception as e:
        print(f"Error:{e}")
        sys.exit()
    return data
class Memory:
    def __init__(self):
        self._ram = [0]*4096
        self._stack = []
        for i in range(len(_FONTSET)):
            self._ram[i] = _FONTSET[i]
    def stack_pop(self):
        return self._stack.pop()
    def stack_push(self,v:int):
        return self._stack.append(v)
    def write_rom_to_ram(self,data:list):
        for i in range(len(data)):
            self._ram[START_ADDR + i] = data[i]
class Display:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("chip8_emulator")
        self.canvas = pygame.display.set_mode((64*10,32*10))
        # self.canvas.fill((0,0,0))
        # pygame.display.update()
    def render(self,screen_buf):
        self.draw_frame(screen_buf)
        pygame.display.update()
    def draw_pixel(self,x:int,y:int):
        pygame.draw.rect(self.canvas,(255,255,255),(x*ZOOM,y*ZOOM,ZOOM,ZOOM),0)
    def draw_frame(self,screen_buf):
        self.canvas.fill((0,0,0))
        for y in range(SCREEN_HEIGHT):
            for x in range(SCREEN_WIDTH):
                if screen_buf[y][x] == 1:
                    self.draw_pixel(x,y)
_KEYS = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
}
class Keyboard:
    def poll_event(self,keys_pressed_buf:list):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                self.key_press(event,keys_pressed_buf)
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
    def key_press(self,event,keys_pressed_buf:list):
        if event.key in _KEYS:
            key = _KEYS[event.key]
            if event.type == pygame.KEYDOWN:
                keys_pressed_buf[key] = 1
            elif event.type == pygame.KEYUP:
                keys_pressed_buf[key] = 0

class CPU:
    def __init__(self):
        self._memory = Memory()
        self._reg_V = [0]*16    # 16个8位通用寄存器，原始类型为uint8
        self._reg_PC = 0x200    # 16位程序指令寄存器指针
        self._reg_index = 0     # 16位索引寄存器

        # self.draw_flag = False  # 保留意见，用途不详
        self._screen_buf = self.reset_screen()  # 显存放大10倍
        self._keys_pressedd_buf = [0]*16 #16个键盘
        self._delay_timer = 0   #延时计时器,60HZ
        self._sound_timer = 0   #声音计时器,60Hz
    def cycle(self):
        self.fetch()
        self.decode()
        self.execute()
    def fetch(self):
        high_byte = self._memory._ram[self._reg_PC]
        low_byte = self._memory._ram[self._reg_PC +1]
        instruction = (high_byte <<8) | low_byte
        self._reg_PC += 2
        self.IR = Instruction(instruction)
    def decode(self):
        self.IR.decode()
    def reset_screen(self):
        return [[0 for _ in range(SCREEN_WIDTH)] for _ in range(SCREEN_HEIGHT)]
    def ticker(self):
        if self._delay_timer > 0:
            self._delay_timer -= 1
        if self._sound_timer > 0:
            self._sound_timer -= 1
            #pygame.mixer.music.play()
    def execute(self):
        # 00E0
        if self.opcode == 0x00:
            if self.kk == 0x00E0:
                self._screen_buf = self.reset_screen()
                # self.draw_flag = True
            if self.kk == 0x00EE:
                self._reg_PC = self._memory.stack_pop()
        # 1NNN
        elif self.opcode == 0x1000:
            addr = self.nnn
            self._reg_PC = addr
        # 2NNN
        elif self.opcode == 0x2000:
            addr = self.nnn
            self._memory.stack_push(self._reg_PC)
            self._reg_PC = addr
        # 3XKK
        elif self.opcode == 0x3000:
            x = self.x
            kk = self.kk
            if self._reg_V[x] == kk:
                self._reg_PC += 2
        # 4XKK
        elif self.opcode == 0x4000:
            x = self.x
            kk = self.kk
            if self._reg_V[x] != kk:
                self._reg_PC += 2
        # 5XY0
        elif self.opcode == 0x5000:
            x = self.x
            y = self.y
            if self._reg_V[x] == self._reg_V[y]:
                self._reg_PC += 2
        # 6XKK
        elif self.opcode == 0x6000:
            x =self.x
            kk =self.kk
            self._reg_V[x] = kk
        # 7XKK
        elif self.opcode == 0x7000:
            x = self.x
            kk = self.kk
            self._reg_V[x] += kk
            self._reg_V[x] &= 0xff
        # 8XYN
        elif self.opcode == 0x8000:
            if self.n == 0x0000:
                x = self.x
                y = self.y
                self._reg_V[x] = self._reg_V[y]
            elif self.n == 0x0001:
                x = self.x
                y = self.y
                self._reg_V[x] |= self._reg_V[y]
            elif self.n == 0x0002:
                x = self.x
                y = self.y
                self._reg_V[x] &= self._reg_V[y]
            elif self.n == 0x0003:
                x = self.x
                y = self.y
                self._reg_V[x] ^= self._reg_V[y]
            elif self.n == 0x0004:
                x = self.x
                y = self.y
                self._reg_V[x] += self._reg_V[y]
                self._reg_V[0xF] = 0x01 if self._reg_V[x]> 0xFF else 0x00
                self._reg_V[x] &= 0xFF
            elif self.n == 0x0005:
                x = self.x
                y = self.y
                self._reg_V[0x0F] = 0x00 if self._reg_V[x] < self._reg_V[y] else 0x01
                self._reg_V[x] -= self._reg_V[y]
                self._reg_V[x] &= 0xFF
            elif self.n == 0x0006:
                x = self.x
                self._reg_V[0x0F] = self._reg_V[x] & 0x01
                self._reg_V[x] >> 1
            elif self.n == 0x0007:
                x = self.x
                y = self.y
                self._reg_V[0x0F] = 0x01 if self._reg_V[x] < self._reg_V[y] else 0x00
                self._reg_V[x] = self._reg_V[y] - self._reg_V[x]
                self._reg_V[x]&= 0xFF
            elif self.n == 0x000E:
                x = self.x
                # self._reg_V[0x0F] = (self._reg_V[x] >> 7) & 0x01
                self._reg_V[0xF] = (self._reg_V[x] & 0x80) >> 7
                self._reg_V[x] = self._reg_V[x] << 1
                self._reg_V[x] &= 0xFF
                # 9XY0
        elif self.opcode == 0x9000:
            x = self.x
            y = self.y
            if self._reg_V[x] != self._reg_V[y]:
                self._reg_PC += 2
        # ANNN
        elif self.opcode == 0xA000:
            addr = self.nnn
            self._reg_index = addr
        # BNNN
        elif self.opcode == 0xB000:
            addr = self.nnn
            self._reg_PC = self._reg_V[0] + addr
        # CXNN
        elif self.opcode == 0xC000:
            x = self.x
            kk = self.kk
            self._reg_V[x] = random.randrange(0,255) & kk
        # DXYN
        elif self.opcode == 0xD000:
            n = self.n
            x = self.x
            y = self.y
            vx = self._reg_V[x]
            vy = self._reg_V[y]
            self._reg_V[0xF] = 0
            for yy in range(n):
                sys_byte = self._memory._ram[self._reg_index + yy]
                for xx in range(8):
                    x_cord = vx + xx
                    y_cord = vy + yy
                    if x_cord < SCREEN_WIDTH and y_cord < SCREEN_HEIGHT:
                        sys_bit = (sys_byte >> (7-xx)) & 0x01
                        if (self._screen_buf[y_cord][x_cord] & sys_bit) == 1:
                            self._reg_V[0xF] = 1
                        self._screen_buf[y_cord][x_cord] ^= sys_bit
            # self.draw_flag = True
        # EX9E and EXA1
        elif self.opcode == 0xE000:
            if self.kk == 0x009E:
                x = self.x
                if self._keys_pressedd_buf[self._reg_V[x]]==1:
                    self._reg_PC += 2
            elif self.kk == 0x00A1:
                x = self.x
                if self._keys_pressedd_buf[self._reg_V[x]] ==0:
                    self._reg_PC += 2
        # FX07 FX15 FX18
        elif self.opcode == 0xF000:
            if self.kk == 0x0007:
                x = self.x
                self._reg_V[x] = self._delay_timer
            elif self.kk == 0x0015:
                x = self.x
                self._delay_timer = self._reg_V[x]
            elif self.kk == 0x0018:
                x = self.x
                self._sound_timer = self._reg_V[x]
            elif self.kk == 0x001E:
                x = self.x
                self._reg_index += self._reg_V[x]
            elif self.kk == 0x000A:
                x = self.x
                pressed = False
                for i in range(16):
                    if self._keys_pressedd_buf[i] ==1:
                        self._reg_V[x] =i
                        pressed = True
                        break
                if not pressed:
                    self._reg_PC -= 2
            elif self.kk == 0x0029:
                x = self.x
                self._reg_index = self._reg_V[x]*5
            elif self.kk == 0x0033:
                x = self.x
                self._memory._ram[self._reg_index] = self._reg_V[x] //100
                self._memory._ram[self._reg_index +1] = (self._reg_V[x]%100) // 10
                self._memory._ram[self._reg_index +2] = (self._reg_V[x]%100) % 10
            elif self.kk == 0x0055:
                x = self.x
                for i in range(x +1):
                    self._memory._ram[self._reg_index +i] = self._reg_V[i]
            elif self.kk == 0x0065:
                x = self.x
                for i in range(x +1):
                    self._reg_V[i] = self._memory._ram[self._reg_index +i]
    def load_rom(self,data:list):
        self._memory.write_rom_to_ram(data)
    @property
    def opcode(self):
        return self.IR.opcode
    @property
    def x(self):
        return self.IR.x
    @property
    def y(self):
        return self.IR.y
    @property
    def n(self):
        return self.IR.n
    @property
    def kk(self):
        return self.IR.kk
    @property
    def nnn(self):
        return self.IR.nnn


class Machine:
    def __init__(self):
        self.cpu = CPU()
        self.display = Display()
        self.keyboard = Keyboard()
    def run(self):
        cycles = 0
        while True:
            self.cpu.cycle()
            self.keyboard.poll_event(self.cpu._keys_pressedd_buf)
            self.display.render(self.cpu._screen_buf)
            cycles += 1
            time.sleep(1 / CLOCK_SPEED)
            if cycles >= CLOCK_SPEED/TIMER_SPEED:
                cycles = 0
                self.cpu.ticker()
    def load_rom(self,rom_files:str):
        data = load_file(rom_files)
        self.cpu.load_rom(data)
class Instruction:
    def __init__(self,val:int):
        self.val = val
    def decode_opcode(self):
        return self.val &0xF000
    def decode_x(self):
        return (self.val &0x0F00)>>8
    def decode_y(self):
        return (self.val &0x00F0)>>4
    def decode_n(self):
        return self.val &0x000F
    def decode_kk(self):
        return self.val &0x00FF
    def decode_nnn(self):
        return self.val &0x0FFF
    def decode(self):
        self.opcode = self.decode_opcode()
        self.x = self.decode_x()
        self.y = self.decode_y()
        self.n = self.decode_n()
        self.kk = self.decode_kk()
        self.nnn = self.decode_nnn()

if __name__ == '__main__':
    machine = Machine()
    machine.load_rom('./roms/OPCODE')
    machine.run()