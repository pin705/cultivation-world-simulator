# Kế Hoạch Tổng Thể Mở Online Kinh Doanh Cho Cultivation World Simulator

Trạng thái: draft v1  
Ngày cập nhật: 2026-04-13  
Mục tiêu: tài liệu tổng hợp một cửa cho founder, product, design, engineering, live-ops  
Tài liệu liên quan:

- `docs/specs/ai-call-inventory.md`
- `docs/specs/online-business-plan.md`
- `docs/specs/online-financial-model.md`
- `docs/specs/online-business-roadmap-90-days.md`
- `docs/specs/ui-ux-shuimo-direction.md`
- `docs/specs/external-control-api.md`

## 1. Mục tiêu tài liệu

Tài liệu này gom tất cả các quyết định quan trọng thành một bản hoàn chỉnh để mở game theo hướng:

- `online`
- `kinh doanh thật`
- `giảm phụ thuộc AI`
- `người chơi tương tác và cạnh tranh với nhau`
- `AI vẫn đủ để thế giới sống động, bất ngờ, có drama`

Đây không phải tài liệu "làm cho vui", cũng không phải tài liệu "MVP cho có".

Đây là tài liệu định hình một sản phẩm có thể:

- vận hành lâu dài
- thu tiền đúng cách
- giữ chi phí AI trong tầm kiểm soát
- tạo retention nhờ tương tác người chơi, không phải chỉ nhờ log và story tự sinh

## 2. Kết luận chiến lược ngắn gọn

Nếu giữ game như hiện tại:

- sim chạy liên tục
- nhiều NPC gọi AI
- người chơi chủ yếu ngồi xem

thì càng online càng dễ lỗ.

Hướng đúng là chuyển game thành:

> một thế giới tu tiên online dạng async, nơi người chơi sở hữu tông môn, nuôi đệ tử chủ lực, cạnh tranh tài nguyên và thứ hạng với người chơi khác, còn AI đóng vai trò tạo biến động, drama và kể chuyện ở các khoảnh khắc đáng tiền.

Nói ngắn hơn:

- `core economy = người chơi cạnh tranh và trả tiền`
- `AI = gia vị cao cấp, không phải động cơ mặc định cho mọi tick`

## 3. Chẩn đoán bản hiện tại

### 3.1 Điểm mạnh hiện tại

Codebase hiện tại đã có sẵn nền tảng rất tốt:

- mô phỏng thế giới giàu hệ thống
- quan hệ xã hội, tông môn, đột phá, bí cảnh, tournament, dynasty
- event stream tự nhiên tạo drama
- map và UI quan sát thế giới đã có
- một phần API control đã thành hình

Fantasy mạnh nhất hiện tại là:

- `một thế giới tu tiên tự sống`

### 3.2 Điểm yếu hiện tại nếu muốn kinh doanh online

Có 4 điểm nghẽn lớn:

#### A. AI cost sai hình

Hiện tại cost tăng theo:

- số NPC
- số world
- số tick
- số event/story

Đây là shape rất xấu cho online business.

#### B. Player agency yếu

Người chơi hiện tại chủ yếu:

- xem
- đọc
- chỉnh vài thứ kiểu admin

Điều đó không đủ để tạo:

- retention
- rivalry
- social competition
- willingness to pay

#### C. Kiến trúc runtime chưa phải online multi-world

Hiện tại vẫn gần kiểu:

- một runtime chính
- một world trong memory
- websocket phát cho cùng một state
- mutation mang chất host/admin

Không thể dùng cấu trúc đó cho public online service.

#### D. Monetization chưa bám vào value

Nếu người chơi trả tiền nhưng phần "vui" chủ yếu do sim tự chạy, thì:

- cost AI tăng
- giá bán khó đẩy lên
- retention yếu
- margin mỏng

## 4. Nguyên tắc kinh doanh phải khóa ngay

### 4.1 Không làm mọi thứ bằng AI

Khóa nguyên tắc:

- AI không được là xương sống của mọi quyết định nhỏ
- AI chỉ dùng ở nơi player cảm nhận được giá trị

### 4.2 Không bán game như một game premium offline bình thường

Vì sản phẩm này có:

- live-ops
- AI cost
- vận hành world
- support

nên phải có:

- recurring revenue
- private world revenue
- premium narrative revenue

### 4.3 Không để người chơi chỉ ngồi nhìn

Muốn cạnh tranh được, mỗi phiên chơi phải có:

- quyết định
- can thiệp
- hậu quả
- cạnh tranh với người khác

### 4.4 Không scale public traffic khi chưa biết margin

Không free-scale sớm.

Phải biết trước:

- cost/world-day
- cost/payer
- contribution margin từng SKU

## 5. Tái định nghĩa sản phẩm

### 5.1 Product thesis

Sản phẩm mới nên được định nghĩa là:

> game online tu tiên dạng async, nơi người chơi điều hành tông môn, nuôi đệ tử chủ lực, tranh tài nguyên và uy danh với người chơi khác trong một thế giới tự biến động.

### 5.2 Vai trò người chơi

Không nên launch bằng mô hình:

- điều khiển một avatar real-time

Nên launch bằng mô hình:

- mỗi người chơi sở hữu `một tông môn`
- mỗi người chơi chọn `một đệ tử chủ lực`
- mỗi người chơi có `một lượng thiên cơ / can thiệp / khí vận giới hạn`

Lý do:

- hợp với thế mạnh world sim hiện tại
- tăng gắn bó với một nhân vật
- tăng agency mà không cần xây combat real-time
- dễ monetize hơn qua sect, lineage, private world

### 5.3 Fantasy cốt lõi cần bán

Sản phẩm phải đồng thời bán được 4 fantasy:

- `quyền lực`: ta có thể ảnh hưởng vận mệnh, tông môn, cục diện thế giới
- `sở hữu`: đây là sect của ta, đệ tử của ta, lịch sử của ta
- `cạnh tranh`: ta tranh tài nguyên, thứ hạng, influence với người chơi khác
- `câu chuyện`: thế giới luôn có drama, biến động, bất ngờ

## 6. Gameplay mới để người chơi thật sự tương tác

### 6.1 Core loop mới

Core loop đề xuất:

1. vào game
2. xem recap ngắn
3. thấy vấn đề / cơ hội
4. ra quyết định
5. thế giới phản ứng
6. quay lại sau để xem hậu quả

### 6.2 Những thứ người chơi phải làm được

Người chơi cần có hành động rõ ràng, không phải chỉ đọc.

Launch command set nên gồm:

- đặt ưu tiên tông môn: tu luyện, bành trướng, thương mại, ngoại giao, phòng thủ
- nuôi đệ tử chủ lực: cấp tài nguyên, công pháp, bế quan, hộ đạo
- chọn phản ứng trước world event: tham chiến, rút lui, tranh bí cảnh, bảo vệ đồng minh
- dùng `fate intervention`: thiên tượng, ẩn thân, cứu viện, truyền cảm ngộ, phá kế đối thủ
- cử đội hình đi nhiệm vụ: chiếm region, tranh động phủ, escort, cướp nguồn lực

### 6.3 Tương tác giữa người chơi với người chơi

Đây là phần bắt buộc nếu muốn cạnh tranh được.

Phải thêm các tầng tương tác sau:

#### A. Cạnh tranh tài nguyên

- tranh region
- tranh hidden domain
- tranh tournament reward
- tranh disciple talent và relic

#### B. Cạnh tranh thứ hạng

- sect prestige
- world contribution
- champion disciple
- season ladder

#### C. Chính trị và ngoại giao

- lập minh
- phản bội
- hỗ trợ ủy nhiệm
- đặt bounty / thù hằn / embargo

#### D. Xung đột gián tiếp

- phá hậu cần
- cướp mission
- can thiệp vào breakthrough timing
- tranh influence ở city / region / sect relations

#### E. Xung đột trực tiếp nhưng async

- war declaration theo chu kỳ
- raid / retaliation
- duel / challenge
- tournament confrontation

### 6.4 Cơ chế để người chơi không phải online 24/7

Game nên là async chứ không phải thời gian thực bắt buộc.

Nhịp tốt:

- server tick mỗi `10-30 phút`
- mỗi batch = `1 tháng ingame`
- người chơi online để ra lệnh, không phải ngồi canh từng giây

Điều này giúp:

- giảm cost
- hợp với mobile/web habits ở VN/SEA
- tạo cảm giác thế giới vẫn sống khi offline

## 7. AI hybrid model: đủ sống động nhưng không đốt tiền

Đây là phần quan trọng nhất.

### 7.1 Nguyên tắc lớn

Phải chuyển từ:

- `mọi NPC quan trọng đều nghĩ bằng AI`

sang:

- `đa số thế giới chạy bằng rules + utility`
- `AI chỉ chạm vào phần player cảm nhận được`

### 7.2 4 tầng vận hành trí tuệ

#### Tầng 1: deterministic core sim

Dùng rule engine cho:

- movement
- harvesting
- training tick
- economy update
- sect upkeep
- relationship drift cơ bản
- scheduling đơn giản

Tầng này là xương sống.

#### Tầng 2: utility / behavior planner

Dùng scoring hoặc behavior tree cho:

- NPC thường
- dân thường
- đệ tử phụ
- cư dân nền

Ví dụ:

- thiếu tài nguyên thì farm
- bị thương thì heal
- gần breakthrough thì bế quan
- sect yếu thì ưu tiên phòng thủ

Không gọi LLM ở đây.

#### Tầng 3: key-character AI

Chỉ dùng cho:

- sect leader
- main disciple của người chơi
- major rival
- champion event
- figure làm đổi cục diện

Dùng AI cho:

- long-term goal refresh
- choice trong major event
- phản ứng với can thiệp của player

#### Tầng 4: narrative AI

Chỉ dùng khi cần kể chuyện:

- breakthrough lớn
- duel
- confession / betrayal
- tournament
- hidden domain
- sect war
- season recap
- personalized recap của đệ tử chủ lực

### 7.3 Những thứ nên bỏ AI trước

Cắt AI ở các chỗ này đầu tiên:

- background conversation
- minor daily event
- low-stakes interaction
- planning của NPC phụ
- story cho routine actions

### 7.4 Những thứ phải giữ AI

Giữ AI ở:

- world recap có cá tính
- major rival behavior
- main disciple narrative
- sect leader major choice
- major world turning points

### 7.5 Rule budget cứng cho AI

Mỗi world phải có:

- `AI budget / day`
- `AI budget / batch`
- `AI budget / premium world tier`

Khi hết budget:

- chuyển sang template text
- giảm story density
- hạ số nhân vật được AI xử lý
- giữ AI cho player-facing moments trước

### 7.6 Mục tiêu cost shape

Mục tiêu sau khi refactor:

- cost không tăng tuyến tính theo mọi NPC nữa
- cost tăng theo:
  - số world
  - số người chơi active
  - số major moments
  - số premium story worlds

Đây mới là shape chấp nhận được.

## 8. Cấu trúc gameplay cạnh tranh nên có để giữ người chơi

### 8.1 Public world

Vai trò:

- kéo cộng đồng
- tạo drama
- tạo ladder
- bán season access

Nhưng không được là SKU nuôi business chính.

### 8.2 Private world

Vai trò:

- profit engine
- retention mạnh
- friend-group fantasy
- nơi dễ kiểm soát AI cost hơn

Nên bán như:

- `shared realm`
- `world riêng cho nhóm`
- `world có lore chỉnh được`

### 8.3 Season structure

Mỗi season nên có:

- start condition
- world modifier
- race for prestige
- season ranking
- season-end reward
- carryover nhẹ, không snowball phá game

### 8.4 Emotional anchor bắt buộc

Mỗi người chơi phải có ít nhất:

- một đệ tử chủ lực
- một rival rõ ràng
- một lời hứa / ambition đang theo đuổi

Nếu không có 3 cái này, người chơi sẽ quay lại chỉ để đọc rồi out.

## 9. Mô hình doanh thu nên dùng

### 9.1 Trụ doanh thu

Trụ chính:

- founder paid cohort
- season access
- standard private world
- story-rich private world
- cosmetic / chronicle packs

### 9.2 Cái nào nuôi business thật

Phải hiểu rất rõ:

- `season access` giúp có payer volume
- `private world` mới là machine tạo margin
- `story-rich private world` là SKU gánh phần AI đắt

### 9.3 Giá đề xuất cho VN-first

Mức đang hợp lý để thử:

- founder paid cohort: `999,000đ`
- season access: `299,000đ`
- standard private world: `990,000đ/tháng`
- story-rich private world: `1,990,000đ/tháng`
- cosmetic / chronicle pack: `99,000đ`

### 9.4 Tư duy đúng về giá

Đừng nghĩ:

- game VN thì phải rẻ

Phải nghĩ:

- nếu AI và live-ops là cost thật thì giá phải phản ánh cost thật

Nếu dưới giá sàn, scale càng lớn càng lỗ.

## 10. Chi phí vận hành thực tế cần nhìn thế nào

### 10.1 4 lớp chi phí

Chi phí hàng tháng chia thành:

- payroll
- AI cost
- infra / storage
- payment / refund / support leakage

### 10.2 Cái đắt nhất

Thường là:

- team
- rồi tới AI

Chứ không phải server.

### 10.3 Muốn thu về nhiều hơn chi ra phải làm gì

#### A. Bán private worlds sớm

Vì:

- margin tốt
- dễ forecast
- nhóm bạn cùng trả tiền

#### B. Tách AI-rich world thành gói premium

Vì:

- AI đắt phải bán riêng
- không thể giấu trong base package rẻ

#### C. Giữ public world trả phí hoặc giới hạn

Vì:

- public world tạo cost sớm hơn revenue

#### D. Dùng local payment rails cho VN

Vì:

- giảm friction
- giữ margin tốt hơn

#### E. Cắt AI nền trước khi scale marketing

Vì:

- mua người dùng vào một hệ cost xấu chỉ làm lỗ nhanh hơn

## 11. Kênh bán và thị trường

### 11.1 Giai đoạn đầu

Tập trung:

- `web direct`
- `VietQR / local payment`
- `Vietnam first`

### 11.2 Không bán trên Steam ở giai đoạn đầu

Khóa nguyên tắc:

- không dùng Steam làm kênh doanh thu đầu tiên
- nếu dùng Steam sau này thì coi là kênh awareness/discovery

### 11.3 SEA sau Việt Nam

Mở SEA sau khi:

- retention ở VN đủ tốt
- cost shape ổn
- payment flow VN đã mượt

## 12. Kiến trúc kỹ thuật phải bổ sung để mở online kinh doanh

### 12.1 Mục tiêu kỹ thuật

Chuyển từ:

- một world global

sang:

- nhiều world instances
- command queue
- snapshot read model
- account ownership
- billing / entitlement / audit

### 12.2 Các module cần có thêm

#### A. Account và entitlement

Phải có:

- users
- sessions
- player profile
- entitlements
- payment events

#### B. World instance layer

Phải có:

- world_instances
- world_memberships
- world lifecycle
- world AI budget

#### C. Command system

Phải có:

- command queue theo từng world
- idempotency
- audit log
- command result

#### D. Snapshot và recap layer

Phải có:

- world snapshots
- player-facing recap projection
- event aggregation

#### E. Commerce / GM / moderation

Phải có:

- entitlement repair
- refund-safe revocation
- world freeze
- manual grant
- content override

### 12.3 Mapping vào repo hiện tại

Các vùng repo nên được mở rộng theo hướng sau:

#### `src/server/runtime/*`

Hiện tại đang là session runtime đơn.

Phải bổ sung:

- world instance manager
- per-world locks
- lifecycle per world

#### `src/server/services/*`

Phải tách thêm:

- account service
- entitlement service
- world membership service
- recap service
- commercial query service

#### `src/server/api/public_v1/*`

Phải thêm:

- auth endpoints
- account query
- world list / world membership
- recap query
- commerce / payment callback
- player command endpoints rõ nghĩa

#### `src/server/loop_runtime.py`

Phải đổi từ:

- một loop cho một world

sang:

- scheduler cho nhiều world
- budget-aware batch stepping

#### `src/classes/ai.py` và các call site liên quan

Phải phân loại:

- call nào giữ
- call nào chuyển sang utility
- call nào chỉ chạy theo trigger
- call nào chỉ chạy cho premium world

#### `web/src/*`

Phải thêm shell mới:

- recap-first
- sect dashboard
- main disciple panel
- intervention UI
- competitive ladder / rivalry views

## 13. Product flow nên đổi như nào

### 13.1 Flow đúng cho commercial launch

Flow đúng:

1. player vào game
2. nhận recap có trọng điểm
3. thấy 1-3 lựa chọn quan trọng
4. ra quyết định
5. có phản hồi ngay
6. nhận kết quả batch sau

### 13.2 Flow sai cần tránh

Flow sai:

1. player vào
2. thấy quá nhiều data
3. mở event log
4. đọc một lúc
5. không biết bấm gì
6. rời game

## 14. Live-ops phải chuẩn bị từ đầu

### 14.1 Vận hành hàng tuần

Phải có nhịp:

- world modifier hàng tuần
- tuning event
- recap quality review
- AI cost dashboard review
- retention review

### 14.2 Công cụ GM

Trước khi scale phải có:

- freeze / unfreeze world
- repair entitlements
- inspect player history
- inspect AI spend theo world
- override unsafe generated content

## 15. KPI phải đo

### 15.1 KPI sản phẩm

- D1 / D7 / D30 retention
- meaningful commands per session
- recap open rate
- average time to first action
- rivalry recurrence
- disciple attachment rate

### 15.2 KPI kinh doanh

- payer conversion
- ARPPU
- private world conversion
- season attach rate
- refund rate
- payment success rate

### 15.3 KPI cost

- AI cost / world-day
- AI cost / payer
- AI cost / premium world
- infra cost / world
- support cost / payer

## 16. Roadmap triển khai đúng cho mục tiêu kinh doanh

### Phase A: 0-30 ngày

Mục tiêu:

- khóa game loop mới
- khóa AI hybrid model
- khóa commercial model

Phải xong:

- player role mới
- command vocabulary
- AI call inventory
- pricing skeleton
- world instance design

### Phase B: 30-60 ngày

Mục tiêu:

- có vertical slice chơi được theo loop mới

Phải xong:

- sect ownership
- main disciple
- interventions
- recap shell
- AI budget telemetry

### Phase C: 60-90 ngày

Mục tiêu:

- có paid-pilot foundation

Phải xong:

- account + entitlement
- VN payment flow
- private world flow
- command queue / snapshot
- commercial shell

### Phase D: sau 90 ngày

Mục tiêu:

- founder paid cohort
- paid pilot
- private worlds
- tuning theo margin và retention

## 17. Quy tắc cắt chi phí nếu lỗ

Cắt theo thứ tự:

1. background story AI
2. AI cho NPC phụ
3. cadence quá dày
4. public world scale
5. content mỹ thuật không tác động chuyển đổi

Không cắt trước:

- core decision loop
- private world stability
- entitlement correctness
- player-facing recap clarity

## 18. Điều kiện để doanh thu lớn hơn chi phí

Muốn lời phải thỏa đồng thời:

### 18.1 Có ít nhất 1 recurring SKU margin tốt

Trong game này đó là:

- private world

### 18.2 Có 1 entry SKU chuyển đổi được payer

Trong game này đó là:

- founder paid cohort
- season access

### 18.3 AI cost bị khóa bằng budget

Nếu không:

- càng đông người chơi càng lỗ

### 18.4 Người chơi có tương tác và cạnh tranh thật

Nếu không:

- retention thấp
- private world khó bán
- season khó giữ người

## 19. Quyết định phải chốt ngay

Khóa ngay các quyết định sau:

- `Có`: async online world
- `Có`: sect owner + main disciple + limited interventions
- `Có`: private world là trụ doanh thu
- `Có`: AI hybrid, không all-AI
- `Có`: VN-first, SEA-next, web-direct
- `Không`: Steam-first revenue
- `Không`: real-time MMO scope
- `Không`: free-scale public world sớm
- `Không`: biến game thành spectator sim trả phí

## 20. Việc nên làm tiếp ngay trong repo

Nếu bắt đầu thi công ngay, thứ tự đúng là:

1. làm `AI call inventory` theo code hiện tại
2. viết `player command spec` mới
3. tách `world instance runtime`
4. thiết kế `recap + sect + disciple` shell mới
5. thêm `VN payment + entitlement` flow
6. dựng `private world` như SKU đầu tiên có thể bán được

## 21. Kết luận cuối

Muốn mở online kinh doanh được thì game này phải đổi trọng tâm:

Từ:

- `xem một thế giới tu tiên tự chạy`

Sang:

- `tham gia, cạnh tranh và điều khiển một thế giới tu tiên đang sống`

Từ:

- `AI cho mọi thứ`

Sang:

- `AI cho những khoảnh khắc đáng tiền`

Từ:

- `public sim tốn tiền`

Sang:

- `private world và premium narrative tạo margin`

Nếu giữ đúng ba chuyển đổi này, game có cửa thành business.
