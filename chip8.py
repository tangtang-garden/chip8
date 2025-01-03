import pygame,sys,time,random,os,array
SCREEN_WIDTH = 64
SCREEN_HEIGHT = 32
ZOOM = 10
START_ADDR = 0x200
FONTSET_START_ADDR = 0x50
CLOCK_SPEED = 1200
TIMER_SPEED = 60
_KEYS = {
    pygame.K_1: 0x1, pygame.K_2: 0x2, pygame.K_3: 0x3, pygame.K_4: 0xC,
    pygame.K_q: 0x4, pygame.K_w: 0x5, pygame.K_e: 0x6, pygame.K_r: 0xD,
    pygame.K_a: 0x7, pygame.K_s: 0x8, pygame.K_d: 0x9, pygame.K_f: 0xE,
    pygame.K_z: 0xA, pygame.K_x: 0x0, pygame.K_c: 0xB, pygame.K_v: 0xF
}
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
class Memory:
    def __init__(self) -> None:
        self.ram = memoryview(bytearray(1024 * 4))  # 4k
        self.stack = array.array('H',range(16))      # 16 bit * 16
        for i in range(len(_FONTSET)):
            self.ram[FONTSET_START_ADDR+i] = _FONTSET[i]
    def write(self,data:list):
        for i in range(len(data)):
            self.ram[START_ADDR + i] = data[i]
class Instruction:
    ...
class Display:
    def __init__(self) -> None:
        pygame.init()
        pygame.display.set_caption("chip8")
        self.canvas = pygame.display.set_mode((64*10,32*10))
        self.canvas.fill((0,0,0))
        pygame.display.update()
    def render(self,screen_Buf:list):
        self.draw_frame(screen_Buf)
        pygame.display.update()
    def draw_frame(self,screen_Buf:list):
        self.canvas.fill((0,0,0))
        for yPos in range(SCREEN_HEIGHT):
            for xPos in range(SCREEN_WIDTH):
                if screen_Buf[yPos * SCREEN_WIDTH + xPos]==1:
                    self.draw_pixel(xPos,yPos)
    def draw_pixel(self,xPos,yPos):
        pygame.draw.rect(self.canvas,(255,255,255),(xPos*ZOOM,yPos*ZOOM,ZOOM,ZOOM),0)
    def quit(self):
        pygame.quit()
class Keyboard:
    def poll_event(self,keys_buf:list):
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN or event.type == pygame.KEYUP:
                self.key_press(event,keys_buf)
            elif event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
    def key_press(self,event,keys_buf:list):
        if event.key in _KEYS:
            key = _KEYS[event.key]
            if event.type == pygame.KEYDOWN:
                keys_buf[key] = 1
            elif event.type == pygame.KEYUP:
                keys_buf[key] = 0
class CPU:
    def __init__(self) -> None: # if reg[x] value > 256,reg[0xF] set 1,so can'y use bytearray
        self.registers = array.array('h',range(16))       # 8 bit*16   
        self.memory = Memory()
        self.regIndex = 0       # 16 bit
        self.regPC = START_ADDR # 16 bit
        self.regSP = 0          # 16 bit
        self.delayTimer = 0     # 8 bit
        self.soundTimer = 0     # 8 bit
        self.keypadBuf = bytearray(16) # [0]*16
        self.screenBuf = self.clearScreenBuf()
        pygame.mixer.music.load(os.path.join(os.path.dirname(__file__),"beep.mp3"))
        self.opcode = 0
        self.table = {
            0x0:self.table0,
            0x1:self.OP_1nnn,
            0x2:self.OP_2nnn,
            0x3:self.OP_3xkk,
            0x4:self.OP_4xKK,
            0x5:self.OP_5xy0,
            0x6:self.OP_6xKK,
            0x7:self.OP_7xkk,
            0x8:self.table8,
            0x9:self.OP_9xy0,
            0xA:self.OP_Annn,
            0xB:self.OP_Bnnn,
            0xC:self.OP_Cxkk,
            0xD:self.OP_Dxyn,
            0xE:self.tableE,
            0xF:self.tableF
        }
        self.table_0={
            0x0:self.OP_00E0,
            0xE:self.OP_00EE
        }
        self.table_8={
            0x0:self.OP_8xy0,
            0x1:self.OP_8xy1,
            0x2:self.OP_8xy2,
            0x3:self.OP_8xy3,
            0x4:self.OP_8xy4,
            0x5:self.OP_8xy5,
            0x6:self.OP_8xy6,
            0x7:self.OP_8xy7,
            0xE:self.OP_8xyE
        }
        self.table_E={
            0x1:self.OP_ExA1,
            0xE:self.OP_Ex9E
        }
        self.table_F={
            0x7:self.OP_Fx07,
            0xA:self.OP_Fx0A,
            0x15:self.OP_Fx15,
            0x18:self.OP_Fx18,
            0x1E:self.OP_Fx1E,
            0x29:self.OP_Fx29,
            0x33:self.OP_Fx33,
            0x55:self.OP_Fx55,
            0x65:self.OP_Fx65
        }
    def clearScreenBuf(self):
        return [0]*SCREEN_HEIGHT*SCREEN_WIDTH
    def OP_00E0(self):
        # 00E0 CLS
        self.screenBuf = self.clearScreenBuf()
    def OP_00EE(self):
        # 00EE RET
        self.regSP -= 1
        self.regPC = self.memory.stack[self.regSP]
    def OP_1nnn(self):
        # JP addr
        addr = self.opcode & 0x0FFF
        self.regPC = addr
    def OP_2nnn(self):
        # Call addr
        addr = self.opcode & 0x0FFF
        self.memory.stack[self.regSP] = self.regPC
        self.regSP += 1
        self.regPC = addr
    def OP_3xkk(self):
        # SE vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        if self.registers[vx] == byte:
            self.regPC += 2
    def OP_4xKK(self):
        # SNE vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        if self.registers[vx] != byte:
            self.regPC += 2
    def OP_5xy0(self):
        # SE vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        if self.registers[vx] == self.registers[vy]:
            self.regPC += 2
    def OP_6xKK(self):
        # LD vx,byte
        vx = (self.opcode & 0x0F00) >> 8
        byte = self.opcode & 0x00FF
        self.registers[vx] = byte
    def OP_7xkk(self):
        # ADD vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        self.registers[vx] += byte
        self.registers[vx] &= 0xFF
    def OP_8xy0(self):
        # LD vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] = self.registers[vy]
    def OP_8xy1(self):
        # OR vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] |= self.registers[vy]
    def OP_8xy2(self):
        # AND vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] &= self.registers[vy]
    def OP_8xy3(self):
        # XOR vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] ^= self.registers[vy]
    def OP_8xy4(self):
        # ADD vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[vx] += self.registers[vy]
        self.registers[0xF] = 1 if self.registers[vx]>0xFF else 0
        self.registers[vx] &= 0xFF
    def OP_8xy5(self):
        # SUB vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[0xF] = 1 if self.registers[vx]>self.registers[vy] else 0
        self.registers[vx] -= self.registers[vy]
        self.registers[vx] &= 0xFF
    def OP_8xy6(self):
        # SHR vx
        vx = (self.opcode & 0x0F00)>>8
        self.registers[0xF] = self.registers[vx] & 0x1
        self.registers[vx] >>=1
    def OP_8xy7(self):
        # SUBN vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        self.registers[0xF] = 0x1 if self.registers[vx] < self.registers[vy] else 0x0
        self.registers[vx] = self.registers[vy] - self.registers[vx]
        self.registers[vx] &= 0xFF
    def OP_8xyE(self):
        # SHL vx {,vy}
        vx = (self.opcode & 0x0F00)>>8
        self.registers[0xF] = (self.registers[vx] & 0x80) >>7
        self.registers[vx] <<= 1
        self.registers[vx] &= 0xFF
    def OP_9xy0(self):
        # SNE vx,vy
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        if self.registers[vx] != self.registers[vy]:
            self.regPC += 2
    def OP_Annn(self):
        # LD I,addr
        addr = self.opcode & 0x0FFF
        self.regIndex = addr
    def OP_Bnnn(self):
        # JP v0,addr
        addr = self.opcode & 0x0FFF
        self.regPC = self.registers[0] + addr
    def OP_Cxkk(self):
        # RND vx,byte
        vx = (self.opcode & 0x0F00)>>8
        byte = self.opcode & 0x00FF
        self.registers[vx] = random.randrange(0,255) & byte
    def OP_Dxyn(self):
        # DRW vx,vy,nibble
        vx = (self.opcode & 0x0F00)>>8
        vy = (self.opcode & 0x00F0)>>4
        height = self.opcode & 0x000F
        xPos = self.registers[vx] % SCREEN_WIDTH
        yPos = self.registers[vy] % SCREEN_HEIGHT
        self.registers[0xF] = 0
        for row in range(height):
            spriteByte = self.memory.ram[self.regIndex + row]
            y_cord = yPos+row
            for col in range(8):
                x_cord = xPos + col
                if y_cord < SCREEN_HEIGHT and x_cord < SCREEN_WIDTH:
                    spritePixel = spriteByte & (0x80 >> col)
                    # spritePixel = (spriteByte >> (7 - col)) & 0x01
                    # if (self.screenBuf[y_cord*SCREEN_WIDTH+x_cord]&spritePixel) == 1:
                    #     self.registers[0xF] = 1
                    # self.screenBuf[y_cord * SCREEN_WIDTH + x_cord] ^= spritePixel
                    screenPixel = self.screenBuf[y_cord*SCREEN_WIDTH + x_cord]
                    if spritePixel:
                        if screenPixel:self.registers[0xF] = 1
                        self.screenBuf[(yPos + row)*SCREEN_WIDTH + (xPos+col)] ^= 1
    def OP_Ex9E(self):
        # SKP vx
        vx = (self.opcode & 0x0F00) >> 8
        key = self.registers[vx]
        if self.keypadBuf[key]:
            self.regPC += 2
    def OP_ExA1(self):
        # SKNP vx
        vx = (self.opcode & 0x0F00) >> 8
        key = self.registers[vx]
        if not self.keypadBuf[key]:
            self.regPC += 2
    def OP_Fx07(self):
        # LD vx,DT
        vx = (self.opcode & 0x0F00) >> 8
        self.registers[vx] = self.delayTimer
    def OP_Fx0A(self):
        # LD vx,k
        vx = (self.opcode & 0x0F00) >> 8
        for i in range(16):
            if self.keypadBuf[i]:
                self.registers[vx] = i
                break
        else:
            self.regPC -= 2
    def OP_Fx15(self):
        # LD Dt,vx
        vx = (self.opcode & 0x0F00) >> 8
        self.delayTimer = self.registers[vx]
    def OP_Fx18(self):
        # LD ST,vx
        vx = (self.opcode & 0x0F00) >> 8
        self.soundTimer = self.registers[vx]
    def OP_Fx1E(self):
        # ADD I,vx
        vx = (self.opcode & 0x0F00) >> 8
        self.regIndex += self.registers[vx]
    def OP_Fx29(self):
        # LD,F,vx
        vx = (self.opcode & 0x0F00) >> 8
        digit = self.registers[vx]
        self.regIndex = FONTSET_START_ADDR+ (5 * digit)
    def OP_Fx33(self):
        # LD B,vx
        vx = (self.opcode & 0x0F00) >> 8
        value = self.registers[vx]
        self.memory.ram[self.regIndex + 2] = value % 10
        value //=10
        self.memory.ram[self.regIndex + 1] = value % 10
        value //=10
        self.memory.ram[self.regIndex] = value % 10
    def OP_Fx55(self):
        # LD [I],vx
        vx = (self.opcode & 0x0F00) >> 8
        for i in range(vx+1):
            self.memory.ram[self.regIndex + i] = self.registers[i]
    def OP_Fx65(self):
        # LD vx,[i]
        vx = (self.opcode & 0x0F00) >> 8
        for i in range(vx + 1):
            self.registers[i] = self.memory.ram[self.regIndex + i]
    def OP_NULL(self):
        ...
    def load_rom(self,data:list):
        self.memory.write(data)
    def table0(self):
        self.table_0[self.opcode&0x000F]()
    def table8(self):
        self.table_8[self.opcode&0x000F]()
    def tableE(self):
        self.table_E[self.opcode&0x000F]()
    def tableF(self):
        self.table_F[self.opcode&0x00FF]()
    def cycle(self):
        self.fetch()
        self.decode()
        self.execute()
    def ticker(self):
        if self.delayTimer > 0:
            self.delayTimer -= 1
        if self.soundTimer > 0:
            self.soundTimer -= 1
            pygame.mixer.music.play()
    def fetch(self):
        high_byte = self.memory.ram[self.regPC]
        low_byte = self.memory.ram[self.regPC + 1]
        self.opcode = (high_byte << 8)|low_byte
        self.regPC += 2
    def decode(self):
        ...
    def execute(self):
        self.table[(self.opcode & 0xF000)>>12]()
class Chip8:
    def __init__(self) -> None:
        self.display = Display()
        self.keyboard = Keyboard()
        self.cpu = CPU()
    def load_rom(self,ch8_file:str):
        data = loadROM(ch8_file)
        self.cpu.load_rom(data)
    def run(self):
        cycles = 0
        while True:
            self.cpu.cycle()
            self.keyboard.poll_event(self.cpu.keypadBuf)
            self.display.render(self.cpu.screenBuf)
            cycles += 1
            time.sleep(1/CLOCK_SPEED)
            if cycles >= CLOCK_SPEED / TIMER_SPEED:
                cycles = 0
                self.cpu.ticker()
    def exit(self):
        self.display.quit()
        sys.exit()

def loadROM(filename):
    data = bytearray()
    with open(filename,'rb') as fin:
        for byte in fin:    # file_bytes = f.read()
            data += byte    # for byte in file_bytes:
                            #     data.append(byte)
    return data

if __name__ == '__main__':
    try:
        chip8 = Chip8()
        chip8.load_rom("TETRIS")
        chip8.run()
    except Exception as e:
        print(f"Err: {e}")