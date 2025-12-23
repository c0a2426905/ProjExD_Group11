import math
import os
import random
import sys
import time
import pygame as pg
import pygame.math as pgm


WIDTH = 1100  # ゲームウィンドウの幅
HEIGHT = 650  # ゲームウィンドウの高さ
os.chdir(os.path.dirname(os.path.abspath(__file__)))


def check_bound(obj_rct: pg.Rect) -> tuple[bool, bool]:
    """
    オブジェクトが画面内or画面外を判定し，真理値タプルを返す関数
    引数：こうかとんや爆弾，ビームなどのRect
    戻り値：横方向，縦方向のはみ出し判定結果（画面内：True／画面外：False）
    """
    yoko, tate = True, True
    if obj_rct.left < 0 or WIDTH < obj_rct.right:
        yoko = False
    if obj_rct.top < 0 or HEIGHT < obj_rct.bottom:
        tate = False
    return yoko, tate


def calc_orientation(org: pg.Rect, dst: pg.Rect) -> tuple[float, float]:
    """
    orgから見て，dstがどこにあるかを計算し，方向ベクトルをタプルで返す
    引数1 org：爆弾SurfaceのRect
    引数2 dst：こうかとんSurfaceのRect
    戻り値：orgから見たdstの方向ベクトルを表すタプル
    """
    x_diff, y_diff = dst.centerx-org.centerx, dst.centery-org.centery
    norm = math.sqrt(x_diff**2+y_diff**2)
    return x_diff/norm, y_diff/norm


class Bird(pg.sprite.Sprite):
    """
    ゲームキャラクター（こうかとん）に関するクラス
    """
    delta = {  # 押下キーと移動量の辞書
        pg.K_UP: (0, -1),
        pg.K_DOWN: (0, +1),
        pg.K_LEFT: (-1, 0),
        pg.K_RIGHT: (+1, 0),
    }

    def __init__(self, num: int, xy: tuple[int, int]):
        """
        こうかとん画像Surfaceを生成する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 xy：こうかとん画像の位置座標タプル
        変数1 state : 無敵状態無し→normal,有り→hyper
        変数2 hyper_life : 無敵状態の残り時間
        """
        self.state = "normal"
        self.hyper_life = 0

        super().__init__()
        img0 = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        img = pg.transform.flip(img0, True, False)  # デフォルトのこうかとん
        self.imgs = {
            (+1, 0): img,  # 右
            (+1, -1): pg.transform.rotozoom(img, 45, 0.9),  # 右上
            (0, -1): pg.transform.rotozoom(img, 90, 0.9),  # 上
            (-1, -1): pg.transform.rotozoom(img0, -45, 0.9),  # 左上
            (-1, 0): img0,  # 左
            (-1, +1): pg.transform.rotozoom(img0, 45, 0.9),  # 左下
            (0, +1): pg.transform.rotozoom(img, -90, 0.9),  # 下
            (+1, +1): pg.transform.rotozoom(img, -45, 0.9),  # 右下
        }
        self.dire = (+1, 0)
        self.image = self.imgs[self.dire]
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.speed = 10

    def change_img(self, num: int, screen: pg.Surface):
        """
        こうかとん画像を切り替え，画面に転送する
        引数1 num：こうかとん画像ファイル名の番号
        引数2 screen：画面Surface
        """
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/{num}.png"), 0, 0.9)
        screen.blit(self.image, self.rect)

    def update(self, key_lst: list[bool], screen: pg.Surface):
        """
        押下キーに応じてこうかとんを移動させる
        引数1 key_lst：押下キーの真理値リスト
        引数2 screen：画面Surface
        """
        ##追加機能1
        if key_lst[pg.K_LSHIFT]:
            self.speed = 20
        else:
            self.speed = 10

        sum_mv = [0, 0]
        for k, mv in __class__.delta.items():
            if key_lst[k]:
                sum_mv[0] += mv[0]
                sum_mv[1] += mv[1]
        self.rect.move_ip(self.speed*sum_mv[0], self.speed*sum_mv[1])
        if check_bound(self.rect) != (True, True):
            self.rect.move_ip(-self.speed*sum_mv[0], -self.speed*sum_mv[1])
        if not (sum_mv[0] == 0 and sum_mv[1] == 0):
            self.dire = tuple(sum_mv)
            self.image = self.imgs[self.dire]

        if self.state == "hyper":
            self.image = pg.transform.laplacian(self.image)
            self.hyper_life -= 1
            if self.hyper_life < 0:
                self.state = "normal"

        screen.blit(self.image, self.rect)


class Beam(pg.sprite.Sprite):
    """
    ビームに関するクラス
    """
    def __init__(self, bird: Bird, angle0: int=0):
        """
        ビーム画像Surfaceを生成する
        引数 bird：ビームを放つこうかとん
        引数 angle0：ビームの回転角度 デフォルトで0
        """
        super().__init__()
        self.vx, self.vy = bird.dire
        angle = math.degrees(math.atan2(-self.vy, self.vx)) + angle0
        self.image = pg.transform.rotozoom(pg.image.load(f"fig/beam.png"), angle, 1.0)
        self.vx = math.cos(math.radians(angle))
        self.vy = -math.sin(math.radians(angle))
        self.rect = self.image.get_rect()
        self.rect.centery = bird.rect.centery+bird.rect.height*self.vy
        self.rect.centerx = bird.rect.centerx+bird.rect.width*self.vx
        self.speed = 10

    def update(self):
        """
        ビームを速度ベクトルself.vx, self.vyに基づき移動させる
        引数 screen：画面Surface
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()


class Explosion(pg.sprite.Sprite):
    """
    爆発に関するクラス
    """
    def __init__(self, obj: "Bullet|Enemy", life: int):
        """
        爆弾が爆発するエフェクトを生成する
        引数1 obj：爆発するBombまたは敵機インスタンス
        引数2 life：爆発時間
        """
        super().__init__()
        img = pg.image.load(f"fig/explosion.gif")
        self.imgs = [img, pg.transform.flip(img, 1, 1)]
        self.image = self.imgs[0]
        self.rect = self.image.get_rect(center=obj.rect.center)
        self.life = life

    def update(self):
        """
        爆発時間を1減算した爆発経過時間_lifeに応じて爆発画像を切り替えることで
        爆発エフェクトを表現する
        """
        self.life -= 1
        self.image = self.imgs[self.life//10%2]
        if self.life < 0:
            self.kill()

class Bullet(pg.sprite.Sprite):
    """
    敵機の爆弾に関するクラス
    """
    def __init__(self, image: pg.Surface, direction: tuple[float, float], pos: tuple[int, int], speed: float):
        """
        敵機が放つ爆弾画像Surfaceを生成する
        引数1 image：爆弾の画像Surface
        引数2 direction：爆弾の進行方向を表すタプル(vx, vy)
        引数3 pos：爆弾の初期位置座標タプル
        引数4 speed：爆弾の速度
        """
        super().__init__()
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.center = pos
        self.vx, self.vy = direction
        self.speed = speed


    def update(self):
        """
        爆弾を速度ベクトルself.vx, self.vyに基づき移動させる
        画面外に出た場合は爆弾を消去する
        """
        self.rect.move_ip(self.speed*self.vx, self.speed*self.vy)
        if check_bound(self.rect) != (True, True):
            self.kill()



class Enemy(pg.sprite.Sprite):
    """
    敵機に関するクラス
    """
    imgs = [pg.image.load(f"fig/alien{i}.png") for i in range(1, 4)]
    bullet_img = pg.image.load("fig/bullet1.png")
    
    def __init__(self):
        """
        敵機画像Surfaceを生成する
        ランダムな敵機画像を選択し、画面上部からランダムな位置に配置する
        """
        super().__init__()
        self.image = pg.transform.rotozoom(random.choice(__class__.imgs), 0, 0.8)
        self.rect = self.image.get_rect()
        self.rect.center = random.randint(0, WIDTH), 0
        self.vx, self.vy = 0, +6
        self.bound = random.randint(50, HEIGHT//2)  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = 50  # 爆弾投下インターバル
        self.bullet_img = __class__.bullet_img
        self.hp = 1 # 敵機の体力

    def update(self):
        """
        敵機を速度ベクトルself.vyに基づき移動（降下）させる
        ランダムに決めた停止位置self.boundまで降下したら、self.stateを停止状態に変更する
        体力が0以下になった場合は敵機を消去する
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)
        if self.hp <= 0:
            self.kill()

    def shoot(self, bird: Bird) -> Bullet:
        """
        敵機がこうかとんに向けて爆弾を放つ
        引数 bird：こうかとん
        戻り値：爆弾インスタンス
        """
        direction = calc_orientation(self.rect, bird.rect)
        return Bullet(self.bullet_img, direction, self.rect.center, 6)

class Boss(Enemy):
    """
    ボス敵機に関するクラス
    """
    
    def __init__(self):
        """
        ボス敵機画像Surfaceを生成する
        画面中央上部から登場し、通常の敵機より高い体力と速い攻撃間隔を持つ
        """
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/boss.png"), 0, 4)
        self.rect = self.image.get_rect()
        self.rect.center = WIDTH//2, -200
        self.vx, self.vy = 0, +3
        self.bound = HEIGHT//4  # 停止位置
        self.state = "down"  # 降下状態or停止状態
        self.interval = 5  # 爆弾投下インターバル
        self.hp = 20 # ボス敵機の体力

        self.bullet_imgs = [pg.image.load("fig/bullet1.png")]

    def update(self):
        """
        ボス敵機を速度ベクトルself.vyに基づき移動（降下）させる
        停止位置self.boundまで降下したら、self.stateを停止状態に変更する
        体力が0以下になった場合はボス敵機を消去する
        """
        if self.rect.centery > self.bound:
            self.vy = 0
            self.state = "stop"
        self.rect.move_ip(self.vx, self.vy)
        if self.hp <= 0:
            self.kill()

    def shoot(self, bird: Bird) -> list[Bullet]:
        """
        ボス敵機がこうかとんに向けて3方向に爆弾を放つ
        引数 bird：こうかとん
        戻り値：爆弾インスタンスのリスト（3個）
        """
        direction = calc_orientation(self.rect, bird.rect)
        angle = math.degrees(math.atan2(-direction[1], direction[0]))
        bullets = []
        for delta_angle in [-20, 0, +20]:
            rad = math.radians(angle + delta_angle)
            dir_x = math.cos(rad)
            dir_y = -math.sin(rad)
            bullets.append(Bullet(self.bullet_imgs[0], (dir_x, dir_y), self.rect.center, 8))
        return bullets   


class Menu:
    """
    メニュー画面に関するクラス
    """
    def __init__(self,screen:pg.Surface):
        self.screen = screen
        self.font_title = pg.font.Font("font/ipaexg.ttf",80)
        self.font_msg = pg.font.Font("font/ipaexg.ttf",40)

    def draw(self):
        """
        メニュー画面を描画する
        """
        self.screen.fill(0)

        title_surf = self.font_title.render("こうかとんゼビウスゲーム",True,(255,255,255))
        msg_surf = self.font_msg.render("SPACEキーでゲーム開始",True,(255,255,255))

        title_rect = title_surf.get_rect(center = (WIDTH//2,HEIGHT//2 - 50))
        msg_rect = msg_surf.get_rect(center = (WIDTH//2,HEIGHT//2 + 100))

        self.screen.blit(title_surf,title_rect)
        self.screen.blit(msg_surf,msg_rect)

class Score:
    """
    スコア表示のクラス
    ゲーム中のポイントを保持し、画面左下に表示する
    value : 現在のスコア
    """
    def __init__(self):
        self.font = pg.font.Font(None, 50)
        self.color = (0, 0, 255)
        self.value = 0
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 100, HEIGHT-50

    def update(self, screen: pg.Surface):
        self.image = self.font.render(f"Score: {self.value}", 0, self.color)
        screen.blit(self.image, self.rect)

class Point(pg.sprite.Sprite):
    """
    ポイントアイテムのクラス
    敵撃破時に確率で出現するポイントアイテムの管理
    """
    def __init__(self, xy: tuple[int, int]):
        super().__init__()
        self.image = pg.transform.rotozoom(pg.image.load("fig/point.png"), 0, 0.1)
        self.rect = self.image.get_rect()
        self.rect.center = xy
        self.vx = 0
        self.vy = 2

    def update(self):
        self.rect.move_ip(self.vx, self.vy)
        if self.rect.top > HEIGHT:
            self.kill()

class Life(pg.sprite.Sprite):
    """
    ライフに関するクラス
    """
    def __init__(self):
        self.font = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 50)
        self.color = (0, 0, 0)
        self.value = 3
        self.invisible_time = 0
        self.image = self.font.render(f"残りライフ：{self.value}", 0, self.color)
        self.rect = self.image.get_rect()
        self.rect.center = 900, 600

    def decrease(self):
        """
        残りライフを減らす関数
        残りライフが0より上でかつ残り無敵時間が0秒以下ならライフを一つ減らす
        """
        if self.invisible_time <= 0 and self.value > 0:
            self.value -= 1
            self.invisible_time = 100  # 約1.5秒から2秒の無敵時間
            self.image = self.font.render(f"残りライフ：{self.value}", 0, self.color)
            self.rect = self.image.get_rect()
            self.rect.center = 900, 600
            return True
        return False
    
    def update(self, screen: pg.Surface):
        if self.invisible_time > 0:
            self.invisible_time -= 1
        self.image = self.font.render(f"残りライフ：{self.value}", 0, self.color)
        screen.blit(self.image, self.rect)


def main():
    pg.display.set_caption("真！こうかとん無双")
    screen = pg.display.set_mode((WIDTH, HEIGHT))

    #追加機能(背景画像スクロール機能)
    # 背景画像を読み込む
    bg_img = pg.image.load(f"fig/haikei.png")
    bg_img = pg.transform.scale(bg_img, (WIDTH, HEIGHT))
    bg_img2 = pg.transform.flip(bg_img, False, True)

    menu = Menu(screen)
    game_mode = "MENU"

    bird = Bird(3, (900, 400))
    beams = pg.sprite.Group()
    exps = pg.sprite.Group()
    emys = pg.sprite.Group()
    life = Life()
    bullets = pg.sprite.Group()

    score = Score()
    points = pg.sprite.Group()

    tmr = 0
    clock = pg.time.Clock()
    while True:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                return 0
            
            if event.type == pg.KEYDOWN and event.key == pg.K_SPACE:
                if game_mode == "MENU":
                    game_mode = "GAME"                             
                elif game_mode == "GAME":
                    beams.add(Beam(bird, 0))    
                    
        if game_mode == "MENU":
                menu.draw()
                pg.display.update()
                clock.tick(50)
                continue

        key_lst = pg.key.get_pressed()              

        #追加機能(背景画像スクロール機能)
        y = tmr % (HEIGHT * 2)
        # 背景を下にスクロール
        screen.blit(bg_img,  (0, y))
        screen.blit(bg_img2, (0, y - HEIGHT))
        screen.blit(bg_img,  (0, y - HEIGHT * 2))

        if tmr%200 == 0:  # 200フレームに1回，敵機を出現させる
            emys.add(Enemy())

        if tmr == 1000:  # 1000フレームでボス登場
            emys.add(Boss())

        for emy in emys:
            if emy.state == "stop" and tmr % emy.interval == 0:
                bullets.add(emy.shoot(bird))

        for emy in pg.sprite.groupcollide(emys, beams, False, True).keys():  # ビームと衝突した敵機リスト
            exps.add(Explosion(emy, 100))  # 爆発エフェクト
            emy.hp -= 1  # 敵機の体力を1減少
            if emy.hp <= 0:
                emy.kill()
                bird.change_img(6, screen)  # こうかとん喜びエフェクト
                score.value += 10  # 敵撃破時の獲得ポイント

                if random.random() < 0.1:  # 敵撃破時のポイントアイテム出現確率
                    points.add(Point(emy.rect.center))

        for bullet in pg.sprite.spritecollide(bird, bullets, True):
            exps.add(Explosion(bullet, 10))  # 爆発エフェクト
        if pg.sprite.spritecollide(bird, points, True):
            score.value += 50  # ポイントアイテム獲得時の獲得ポイント
        
        for bomb in pg.sprite.spritecollide(bird, bullets, True):  # こうかとんと衝突した爆弾リスト
            if getattr(bomb,"state","active") == "active":
                bird.change_img(8, screen)  # こうかとん悲しみエフェクト
                life.decrease()
                pg.display.update()
            if life.value <= 0:
                fonto = pg.font.SysFont("hgp創英角ﾎﾟｯﾌﾟ体", 80)
                txt = fonto.render("ゲームオーバー", True, (255, 0, 0))
                screen.blit(txt, [WIDTH//2-250, HEIGHT//2])
                pg.display.update()
                time.sleep(1)
                return

        
        bird.update(key_lst, screen)
        beams.update()
        beams.draw(screen)
        emys.update()
        emys.draw(screen)
        bullets.update()
        bullets.draw(screen)
        exps.update()
        exps.draw(screen)
        life.update(screen)
        score.update(screen)
        points.update()
        points.draw(screen)
        pg.display.update()
        tmr += 1
        clock.tick(50)


if __name__ == "__main__":
    pg.init()
    main()
    pg.quit()
    sys.exit()
