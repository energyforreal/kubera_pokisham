# Quick Start: Hybrid UI Testing Guide

## 🚀 Getting Started

### 1. Start the Development Server

```bash
cd frontend_web
npm run dev
```

The dashboard will be available at `http://localhost:3000`

### 2. Verify Installation

Check that all packages are installed:
```bash
npm list antd @ant-design/icons @radix-ui/react-select @radix-ui/react-tabs
```

You should see all packages listed without errors.

---

## ✅ Testing Checklist

### Shadcn UI Components

Navigate to different sections of the dashboard and verify:

#### ✅ Button Component
- [ ] Look for buttons throughout the app
- [ ] Hover states work (color transitions)
- [ ] Different variants visible (default, outline, ghost, destructive)
- [ ] Loading state shows spinner (in TradeButton modal)

#### ✅ Card Component
- [ ] All sections use the Card component
- [ ] Dark theme styling applied (dark backgrounds, borders)
- [ ] CardHeader, CardTitle, CardContent properly structured

#### ✅ Dialog Component
- [ ] Click "Execute Trade" button (top right)
- [ ] Modal opens with proper sizing
- [ ] Close button (X) works
- [ ] Backdrop blur visible

#### ✅ Badge Component
- [ ] "Critical" badge in Risk Settings
- [ ] Different color variants visible

#### ✅ Tooltip Component (if used)
- [ ] Hover over icons to see tooltips
- [ ] Arrow pointer visible
- [ ] Dark theme applied

### Ant Design Components

#### ✅ TradeHistory Tab
Navigate to **Trade History** tab:

**Table Features:**
- [ ] Table displays with dark theme styling
- [ ] Click column headers to sort (Date, Price, P&L)
- [ ] Use filter dropdowns on Symbol and Side columns
- [ ] Change page size (bottom right pagination)
- [ ] Horizontal scroll works on mobile/narrow screens

**Statistics:**
- [ ] Four stat cards at top (Total Trades, Win Rate, Total P&L, Avg P&L)
- [ ] Green/red colors based on positive/negative values
- [ ] Arrow icons show trend direction

**Segmented Control:**
- [ ] Toggle between All/Profit/Loss filters
- [ ] Table updates accordingly

#### ✅ RiskSettings Tab
Navigate to **Settings** tab:

**Form Features:**
- [ ] Click "Edit Settings" button
- [ ] All inputs become editable
- [ ] InputNumber fields show formatted values (%, x, :1)
- [ ] Slider for confidence level has marks at 50%, 65%, 75%, 100%
- [ ] Hover tooltips show on field labels (ℹ icon)
- [ ] Click "Save Changes" - shows loading state
- [ ] Validation errors appear for invalid values (try entering -1)
- [ ] Cancel button resets form

**Visual Elements:**
- [ ] Dividers separate sections ("Loss Protection", "Trade Parameters")
- [ ] Warning alert at bottom about restart requirement
- [ ] Badge shows "Critical" warning
- [ ] All inputs have proper dark theme styling

---

## 🎨 Theme Verification

### Dark Mode Check
- [ ] Background is dark (`#0a0e27`)
- [ ] Cards have dark surface color (`#1f2937`)
- [ ] Borders are subtle gray (`#374151`)
- [ ] Text is white/light gray
- [ ] Accent colors are vibrant (cyan, green, red, orange, purple)

### Ant Design Theme Check
- [ ] Ant Design components match overall dark theme
- [ ] Table headers are darker than table body
- [ ] Form inputs have dark backgrounds
- [ ] Buttons use cyan primary color
- [ ] No white/light backgrounds anywhere

---

## 🐛 Common Issues & Solutions

### Issue 1: Components Not Rendering
**Symptoms:** Blank page or missing components

**Solutions:**
1. Check browser console for errors
2. Verify backend API is running (`http://localhost:8000`)
3. Clear cache and refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)

### Issue 2: Styling Not Applied
**Symptoms:** White backgrounds, missing colors

**Solutions:**
1. Verify `className="dark"` in `<html>` tag
2. Check Tailwind CSS is building properly
3. Restart dev server

### Issue 3: TypeScript Errors
**Symptoms:** Red squiggly lines, build failures

**Solutions:**
1. Run: `npm install` (ensure all packages installed)
2. Restart TypeScript server in VS Code: `Ctrl+Shift+P` → "TypeScript: Restart TS Server"
3. Check `tsconfig.json` is present

### Issue 4: Ant Design Components Not Styled
**Symptoms:** Ant Design components have default (light) styling

**Solutions:**
1. Verify `AntdProvider` wraps app in `layout.tsx`
2. Check `globals.css` has Ant Design overrides
3. Clear `.next` cache: `rm -rf .next` and restart dev server

---

## 📊 Component Showcase

### Test All New Components

Create a test page to verify all components work:

```tsx
// app/test-components/page.tsx
'use client';

import { Button } from '@/components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Checkbox } from '@/components/ui/checkbox';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import { Alert, AlertTitle, AlertDescription } from '@/components/ui/alert';
import { Skeleton } from '@/components/ui/skeleton';
import { Slider } from '@/components/ui/slider';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';

export default function TestPage() {
  return (
    <div className="p-8 space-y-8 bg-dark-bg min-h-screen">
      <h1 className="text-3xl font-bold text-white">Component Showcase</h1>
      
      <Card>
        <CardHeader>
          <CardTitle>Buttons</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-4">
          <Button variant="default">Default</Button>
          <Button variant="destructive">Destructive</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="success">Success</Button>
          <Button variant="warning">Warning</Button>
          <Button loading>Loading</Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Badges</CardTitle>
        </CardHeader>
        <CardContent className="flex gap-2">
          <Badge variant="default">Default</Badge>
          <Badge variant="success">Success</Badge>
          <Badge variant="warning">Warning</Badge>
          <Badge variant="destructive">Error</Badge>
          <Badge variant="info">Info</Badge>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Form Elements</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <Label>Text Input</Label>
            <Input placeholder="Enter text..." />
          </div>
          
          <div className="flex items-center gap-2">
            <Switch id="switch" />
            <Label htmlFor="switch">Enable feature</Label>
          </div>
          
          <div className="flex items-center gap-2">
            <Checkbox id="checkbox" />
            <Label htmlFor="checkbox">Accept terms</Label>
          </div>
          
          <div>
            <Label>Slider</Label>
            <Slider defaultValue={[50]} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Progress & Loading</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Progress value={60} />
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-3/4" />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Alerts</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <Alert variant="default">
            <AlertTitle>Info</AlertTitle>
            <AlertDescription>This is an info message</AlertDescription>
          </Alert>
          
          <Alert variant="success">
            <AlertTitle>Success</AlertTitle>
            <AlertDescription>Operation completed successfully</AlertDescription>
          </Alert>
          
          <Alert variant="warning">
            <AlertTitle>Warning</AlertTitle>
            <AlertDescription>Please review this action</AlertDescription>
          </Alert>
          
          <Alert variant="destructive">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>Something went wrong</AlertDescription>
          </Alert>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Tabs</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="tab1">
            <TabsList>
              <TabsTrigger value="tab1">Tab 1</TabsTrigger>
              <TabsTrigger value="tab2">Tab 2</TabsTrigger>
              <TabsTrigger value="tab3">Tab 3</TabsTrigger>
            </TabsList>
            <TabsContent value="tab1">Content for Tab 1</TabsContent>
            <TabsContent value="tab2">Content for Tab 2</TabsContent>
            <TabsContent value="tab3">Content for Tab 3</TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      <Separator />

      <p className="text-gray-400 text-center">
        All Shadcn components are working! ✅
      </p>
    </div>
  );
}
```

Visit `http://localhost:3000/test-components` to see all components.

---

## 📝 Notes

### Performance
- First load may take a few seconds (Next.js compilation)
- Hot reload should be fast after initial load
- Ant Design CSS-in-JS has minimal performance impact

### Browser Compatibility
- Works in all modern browsers (Chrome, Firefox, Safari, Edge)
- Requires JavaScript enabled
- Best experience in Chrome/Edge (latest)

### Mobile Testing
- Responsive design works on all screen sizes
- Table scrolls horizontally on mobile
- Touch interactions work properly
- Test in Chrome DevTools mobile emulation

---

## 🎯 Success Criteria

Your implementation is working correctly if:

✅ All components render without errors
✅ Dark theme is consistent across all components
✅ Shadcn and Ant Design components coexist peacefully
✅ Forms validate properly
✅ Tables sort and filter correctly
✅ Animations are smooth
✅ No console errors
✅ TypeScript compilation succeeds
✅ Mobile responsive design works

---

## 🔗 Next Steps

1. **Customize Colors**: Edit `tailwind.config.js` and `src/providers/antd-registry.tsx`
2. **Add More Components**: Use the guidelines in `src/lib/ui-guidelines.md`
3. **Optimize Performance**: Lazy load heavy components with `dynamic()`
4. **Add Testing**: Write unit tests for new components
5. **Deploy**: Build for production with `npm run build`

---

## 📞 Support

If you encounter issues:
1. Check browser console for errors
2. Review `HYBRID_UI_IMPLEMENTATION_COMPLETE.md`
3. Read `src/lib/ui-guidelines.md`
4. Check Ant Design docs: https://ant.design/
5. Check Shadcn docs: https://ui.shadcn.com/

---

**Happy Testing! 🚀**

