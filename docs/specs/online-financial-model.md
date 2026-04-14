# Cultivation World Simulator Online Financial Model

Status: draft v1  
Owner: founder / finance / product shared model  
Updated: 2026-04-13  
Related:

- `docs/specs/online-business-plan.md`
- `docs/specs/online-business-roadmap-90-days.md`

## 1. Purpose

This document translates the business plan into a commercial financial model.

Its job is to answer five practical questions:

1. what should we actually sell
2. what price floor keeps the product commercially sane
3. which channel should carry which SKU
4. what unit economics must be true before scale
5. how many payers or private worlds are needed to break even

### 1.1 Launch market scope

This model assumes:

- no game sales on Steam in the first commercial phase
- Vietnam is the first real market
- Southeast Asia expansion comes after Vietnamese unit economics are proven
- the primary commercial path is `web direct`

## 2. Commercial Position

This product should be run as a `live premium service`, not as a cheap one-time toy.

The financial implication is simple:

- one-time access alone is not enough
- recurring revenue must exist
- AI-rich modes must be explicitly budgeted into price
- private worlds should be treated as the main profit engine

## 2.1 Regional commercial thesis

For a Vietnam-first and SEA-next launch, the cleanest commercial shape is:

- public participation sold as a paid season or paid cohort
- private worlds sold as recurring subscriptions
- cosmetics and chronicle products sold as ARPPU expansion
- local payment rails used first to preserve margin

This is better than:

- free public access with unknown AI cost
- cheap one-time premium purchase
- Steam-first discovery with platform-taxed revenue

## 3. Recommended Revenue Architecture

The recommended revenue stack is:

### 3.1 SKU A: founder paid cohort

Purpose:

- fund early operations
- create a committed high-signal audience
- validate willingness to pay before broader rollout

Recommended price:

- `799,000đ to 1,290,000đ`

Do not go below:

- `599,000đ`

Suggested content:

- early access to paid pilot worlds
- founder-exclusive seal / title / chronicle frame
- one season of premium access
- discount or bonus for one private world month

### 3.2 SKU B: season access

Purpose:

- monetize public/shared world participation
- align revenue with live season cadence

Recommended cadence:

- `8-week season`

Recommended price:

- `299,000đ to 399,000đ per season`

Do not go below:

- `199,000đ per season`

Notes:

- this SKU works best if the public world is meaningful, competitive, and recap-rich
- if the public world remains low-agency, this SKU will underperform

### 3.3 SKU C: standard private world

Purpose:

- recurring high-margin revenue
- low-noise, high-attachment environment for small groups

Recommended price:

- `990,000đ per month`

Do not go below:

- `699,000đ per month`

Intended value:

- one private world
- controlled simulation speed
- predictable AI budget
- custom lore or ruleset light options

### 3.4 SKU D: story-rich private world

Purpose:

- sell premium narrative density and higher ops budget to the segment that wants it

Recommended price:

- `1,990,000đ per month`

Do not go below:

- `1,490,000đ per month`

Intended value:

- richer story generation
- higher event density
- stronger recap quality
- advanced world settings and export perks

### 3.5 SKU E: cosmetics and premium chronicle items

Purpose:

- increase ARPPU without distorting fairness

Recommended price bands:

- `99,000đ to 249,000đ` for supporter / cosmetic packs
- `49,000đ to 99,000đ` for smaller thematic packs

## 4. Recommended Channel Strategy

### 4.1 Web direct and local payments

Use web direct for:

- private world subscriptions
- founder cohort sales
- premium story-world subscriptions
- direct customer relationship and better margin

Why:

- lower fee burden than platform stores in many cases
- easier recurring billing control
- easier bundling and entitlement logic

For Vietnam-first rollout:

- prioritize `VietQR / bank transfer / local payment automation`
- use SePay or an equivalent local payment layer for fast confirmation, webhook automation, and low payment friction

Official SePay pricing and product pages currently describe:

- a `0đ/tháng` free tier with `50 giao dịch/tháng`
- a `120,000đ/tháng` startup tier
- webhook / API support
- a payment-gateway style flow with no per-transaction payment gateway fee on the page's positioning

### 4.2 SEA expansion path

Use regional or card-based payment rails for:

- English-speaking SEA buyers
- countries where direct Vietnam bank-transfer UX is too weak
- higher-value subscriptions where card acceptance matters

Principle:

- Vietnam economics should be proven first
- do not overbuild a multi-country payments stack before Vietnamese conversion and retention are real

### 4.3 Steam policy for this model

For this commercial model:

- Steam is not a sales assumption
- Steam revenue is excluded from break-even math
- if Steam is used later, treat it as awareness and discovery unless the commercial strategy changes

### 4.4 Recommended split

Best commercial split for this product:

- web direct handles all initial revenue
- Vietnam local payment rails preserve margin
- SEA cross-border methods are added only after local economics are stable

## 5. Pricing Recommendation Summary

| SKU | Recommended | Hard floor | Primary goal |
|---|---:|---:|---|
| Founder paid cohort | 999,000đ | 599,000đ | upfront cash + high-signal users |
| Season access | 299,000đ | 199,000đ | public world recurring revenue |
| Standard private world | 990,000đ/tháng | 699,000đ/tháng | core profit engine |
| Story-rich private world | 1,990,000đ/tháng | 1,490,000đ/tháng | premium margin for AI-rich usage |
| Cosmetic / chronicle pack | 99,000đ | 49,000đ | ARPPU uplift |

## 5.1 Affordability by group size

Private worlds become much more attractive when sold as group-owned subscriptions.

Examples:

- `990,000đ` standard private world split by `5 players` = `198,000đ/player/month`
- `1,990,000đ` story-rich private world split by `8 players` = about `249,000đ/player/month`

Commercial reading:

- private worlds are expensive as a solo SKU
- private worlds are reasonable as a group vanity / community SKU
- the product should market private worlds as a `shared realm`, not only as a solo purchase

## 6. Unit Economics Formulas

### 6.1 Vietnam direct-payment net revenue

Using a low-fee local payment rail model:

- `gateway allocation = monthly gateway cost / monthly transaction count`
- `net cash before refunds/support = price - gateway allocation`

Then:

- `contribution = net cash - variable AI - variable infra - support reserve - refund reserve`

### 6.2 Cross-border card fallback

If you need card-based collection for SEA buyers, use a separate model.

- `processor fee = price x card_processor_rate + fixed_fee`
- `contribution = price - processor fee - variable AI - variable infra - support reserve`

For conservative planning, card-based cross-border transactions should be treated as a lower-margin secondary path, not your default VN revenue path.

### 6.3 Break-even formula

- `required monthly contribution = monthly operating burn`
- `required paying units = monthly operating burn / contribution per paying unit`

Examples:

- `required standard private worlds = burn / contribution_per_standard_world`
- `required story-rich worlds = burn / contribution_per_story_world`
- `required season payers = burn / monthlyized_contribution_per_season_payer`

## 6.4 Monthly operating cost stack

When operating this game, monthly cost should be viewed in four layers.

### Layer A: payroll

This is the largest fixed cost.

Typical functions:

- product / founder
- gameplay engineer
- backend / platform engineer
- frontend engineer
- UI / UX / art
- ops / QA / support

Rule:

- if payroll is not covered, the business is not healthy even if infra looks cheap

### Layer B: AI cost

This is the most dangerous variable cost because it can scale invisibly.

Primary drivers:

- number of active worlds
- story density
- number of premium narrative features
- number of high-value NPCs using LLM

Rule:

- treat AI as a premium-content budget, not as default simulation budget

### Layer C: infra and storage

This includes:

- app servers
- workers
- databases
- snapshot storage
- logs / telemetry

Rule:

- infra should scale slower than payer growth
- if infra scales faster than payer growth, architecture or world cadence is wrong

### Layer D: payment, refund, and support leakage

This includes:

- payment rails
- refund losses
- manual settlement effort
- customer support time

Rule:

- in VN-first operation, local payment rails can keep this layer relatively low
- if support becomes expensive, UX and entitlement handling are the real problem

## 7. Worked Unit Economics

These are planning examples, not guarantees.

### 7.1 Season access example

Assume:

- price `299,000đ`
- average gateway allocation `3,000đ`
- season length `56 days`
- support + refund reserve `20,000đ per payer per season`
- direct variable AI + infra target `60,000đ per payer per season`

Then:

- payment allocation = about `3,000đ`
- net cash before reserves = about `296,000đ`
- contribution after reserves and variable cost = about `216,000đ per season`
- monthlyized contribution = about `108,000đ per payer-month`

Commercial reading:

- season access is useful, but by itself it is not enough to carry the business unless payer volume is large

### 7.2 Standard private world example

Assume:

- price `990,000đ/month`
- average gateway allocation `5,000đ`
- variable AI + infra + storage target `250,000đ/month`
- support reserve `40,000đ/month`

Then:

- payment allocation = about `5,000đ`
- net cash before reserves = about `985,000đ`
- contribution after variable cost and support reserve = about `695,000đ/month`

Commercial reading:

- this is a healthy recurring SKU and should be treated as the primary business backbone

### 7.3 Story-rich private world example

Assume:

- price `1,990,000đ/month`
- average gateway allocation `5,000đ`
- variable AI + infra target `600,000đ/month`
- support reserve `60,000đ/month`

Then:

- payment allocation = about `5,000đ`
- net cash before reserves = about `1,985,000đ`
- contribution after variable cost and support reserve = about `1,325,000đ/month`

Commercial reading:

- this SKU can safely carry higher narrative richness and become your premium margin product

### 7.4 Founder paid cohort example

Assume:

- price `999,000đ`
- average gateway allocation `5,000đ`
- one-time support / ops reserve `50,000đ`

Then:

- payment allocation = about `5,000đ`
- net cash before reserve = about `994,000đ`
- contribution after reserve = about `944,000đ`

Commercial reading:

- founder sales are excellent for upfront runway
- founder sales are not a substitute for recurring revenue

## 8. Recommended Margin Gates

No SKU should be kept live if it violates these gates for multiple weeks without a clear fix path.

### 8.1 Public season / access SKUs

Targets:

- direct cost <= `35%` of net cash
- AI + infra <= `25%` of net cash
- support + refunds <= `10%` of net cash

### 8.2 Standard private world

Targets:

- direct cost <= `30%` of net cash
- AI + infra <= `22%` of net cash
- support <= `8%` of net cash

### 8.3 Story-rich private world

Targets:

- direct cost <= `35%` of net cash
- AI + infra <= `28%` of net cash
- support <= `8%` of net cash

### 8.4 Red flags

Immediate warning signs:

- AI spend > `20%` of gross revenue overall
- any private world SKU contributes less than `500,000đ/month`
- season access contribution falls below `80,000đ/payer-month`
- payment and refund leakage together exceed `15%` of cash collected

## 8.1 The simple rule for revenue > cost

To make revenue exceed cost, you do not need every SKU to be huge.

You need:

1. one strong recurring margin SKU
2. one entry SKU that converts enough paying users
3. strict control of AI and support leakage

For this product, the correct economic shape is:

- `season access` brings in paid users and keeps the world alive
- `private worlds` generate most of the real contribution margin
- `story-rich private worlds` subsidize heavier AI usage
- `founder paid cohort` gives early cash but is not the long-term engine

If this product tries to live only on cheap public access, it will likely be underpriced relative to AI and live-ops cost.

## 8.2 What to do so money comes back more than it goes out

The highest-value actions are:

### A. Sell private worlds early

Why:

- much stronger contribution margin than season-only revenue
- emotionally sticky for friend groups
- easier to forecast cost per world

### B. Price AI-rich experiences as premium

Why:

- the expensive part of the product is narrative richness
- if premium narrative is bundled into cheap base access, margin gets destroyed

### C. Keep public worlds paid or tightly capped at first

Why:

- public worlds create cost before they create margin
- free scale will hide the true cost problem until it is too late

### D. Use Vietnam-first local payment rails

Why:

- lower friction for the target market
- lower payment drag than many cross-border card flows
- easier to keep contribution margin healthy

### E. Reduce passive AI spending before buying users

Why:

- buying users into a lossy cost structure just scales losses faster

## 8.3 What should be cut first if cost is too high

Cut in this order:

1. background story generation
2. non-essential LLM decisions for minor NPCs
3. over-frequent world cadence
4. low-converting public-world scale
5. nice-to-have premium art content

Avoid cutting first:

- the core player decision loop
- private world reliability
- payment confirmation and entitlement correctness

## 9. Burn and Break-Even Planning

### 9.1 Monthly burn formula

Let:

- `X = average loaded monthly cost per FTE`
- `F = active FTE count`
- `O = non-payroll overhead multiplier`

Then:

- `monthly burn = (X x F) x (1 + O) + monthly AI baseline + monthly infra baseline`

Recommended planning `O`:

- `20% to 40%`

### 9.2 Example burn scenarios

#### Example A: Vietnam-first lean team

Assume:

- `X = 60,000,000đ`
- `F = 5`
- `O = 30%`
- non-payroll AI + infra baseline = `90,000,000đ/month`

Then:

- payroll = `300,000,000đ/month`
- loaded team cost = `390,000,000đ/month`
- total monthly burn = about `480,000,000đ/month`

#### Example B: hybrid regional team

Assume:

- `X = 100,000,000đ`
- `F = 5`
- `O = 30%`
- non-payroll AI + infra baseline = `140,000,000đ/month`

Then:

- payroll = `500,000,000đ/month`
- loaded team cost = `650,000,000đ/month`
- total monthly burn = about `790,000,000đ/month`

These are illustrative examples only. Replace them with your real cost base.

## 10. Break-Even Scenarios

### 10.1 If the business is season-led

Using `108,000đ` monthlyized contribution per season payer:

- to cover `480,000,000đ/month`, you need about `4,445` active season payers
- to cover `790,000,000đ/month`, you need about `7,315` active season payers

Commercial reading:

- a season-only model is risky for a niche live sim unless player volume is very large

### 10.2 If the business is standard-private-world-led

Using `695,000đ` contribution per standard private world:

- to cover `480,000,000đ/month`, you need about `691` standard private worlds
- to cover `790,000,000đ/month`, you need about `1,137` standard private worlds

Commercial reading:

- standard private worlds matter a lot, but alone they are still a demanding scale target

### 10.3 If the business is story-world-led

Using `1,325,000đ` contribution per story-rich private world:

- to cover `480,000,000đ/month`, you need about `363` story-rich private worlds
- to cover `790,000,000đ/month`, you need about `597` story-rich private worlds

Commercial reading:

- this is far more plausible than trying to live only on season access
- it also reinforces why high-AI premium modes must be priced confidently

### 10.4 Recommended mixed commercial target

For a `480,000,000đ/month` burn example, a healthier target mix could be:

- `1,500` season payers x `108,000đ` = `162,000,000đ`
- `220` standard private worlds x `695,000đ` = `152,900,000đ`
- `125` story-rich private worlds x `1,325,000đ` = `165,625,000đ`

Total contribution:

- about `480,525,000đ/month`

Commercial reading:

- this mix is much more realistic than relying on one SKU alone

## 11. Pricing Strategy by Phase

### 11.1 Paid founder cohort

Recommended:

- `999,000đ`

Goal:

- maximize signal quality, not volume at any cost

### 11.2 Paid pilot phase

Recommended:

- keep public participation paid or tightly capped
- start private worlds early
- do not use free scale to discover cost problems

### 11.3 First revenue release

Recommended stack:

- season access
- standard private world
- story-rich private world
- first cosmetic pack

### 11.4 Later scaled launch

Only after unit economics are stable:

- consider a free front door
- consider broader acquisition
- consider more generous public-world exposure

## 12. What Not to Do Financially

- do not price the game like a normal offline indie premium title if AI and live ops remain core costs
- do not underprice private worlds just to chase user count
- do not hide expensive narrative modes inside a cheap universal package
- do not scale public-world concurrency before cost-per-payer is known
- do not assume SEA cross-border card collection should be the default VN payment path

## 13. Decision Rules

### 13.1 Raise price if

- AI-rich private worlds are selling but margin is thin
- support load is higher than modeled
- demand remains strong after cohort caps

### 13.2 Cut cost before scaling if

- season payer contribution is below target
- private world direct cost exceeds guardrails
- AI spend rises faster than payer growth

### 13.3 Pause growth if

- refunds are elevated
- public loop is not sticky
- private worlds are not converting
- support burden is operationally unsafe

## 14. Spreadsheet Template Fields

At minimum, track these inputs:

- SKU price
- payment fee percentage
- fixed fee per transaction
- refund reserve
- support reserve
- AI variable cost per user or world
- infra variable cost per user or world
- monthly fixed burn
- payer count by SKU

Outputs:

- net cash by SKU
- contribution by SKU
- blended gross margin
- required payers to break even
- break-even month

## 15. Recommended Immediate Finance Actions

1. decide the initial founder cohort price
2. decide the launch private-world price floor and refuse to undercut it
3. instrument cost-per-world-day before any broader paid pilot
4. build a spreadsheet using the formulas in this document
5. review contribution margin weekly during paid operation

## 16. Source Assumptions

Current official references used for this model:

- DeepSeek pricing: [api-docs.deepseek.com/quick_start/pricing](https://api-docs.deepseek.com/quick_start/pricing/)
- SePay pricing: [sepay.vn/bang-gia.html](https://sepay.vn/bang-gia.html)
- SePay product overview: [sepay.vn/en](https://sepay.vn/en)
- Stripe pricing for cross-border card fallback: [stripe.com/pricing](https://stripe.com/pricing)
