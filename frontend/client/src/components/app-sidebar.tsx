import { cn } from '@/lib/utils';
import { LogoIcon } from '@/components/logo';
import {
  Sidebar,
  SidebarContent,
  SidebarFooter,
  SidebarHeader,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
} from '@/components/ui/sidebar';
import { Link } from 'react-router-dom';
import { guestNavGroups, footerNavLinks, memberNavGroup, isNavItemActive, useAppPath, useShellUser } from '@/components/app-shared';
import { NavGroup } from '@/components/nav-group';

export function AppSidebar() {
  const path = useAppPath();
  const user = useShellUser();
  const groups = [...guestNavGroups, ...(user ? [memberNavGroup] : [])];

  return (
    <Sidebar
      className={cn(
        '*:data-[slot=sidebar-inner]:bg-background',
        '*:data-[slot=sidebar-inner]:dark:bg-[radial-gradient(60%_18%_at_10%_0%,--theme(--color-foreground/.08),transparent)]',
        '**:data-[slot=sidebar-menu-button]:[&>span]:text-foreground/75',
      )}
      collapsible="icon"
      variant="sidebar"
    >
      <SidebarHeader className="h-14 justify-center border-b px-2">
        <SidebarMenuButton asChild>
          <Link to="/" aria-label="AnimeTracker 首页">
            <LogoIcon />
            <span className="font-medium text-foreground!">AnimeTracker</span>
          </Link>
        </SidebarMenuButton>
      </SidebarHeader>
      <SidebarContent>
        {groups.map((group, index) => (
          <NavGroup key={`sidebar-group-${index}`} label={group.label} items={group.items.map((item) => ({ ...item, isActive: isNavItemActive(path, item.path) }))} />
        ))}
      </SidebarContent>
      <SidebarFooter className="gap-0 p-0">
        <SidebarMenu className="border-t p-2">
          {footerNavLinks.map((item) => (
            <SidebarMenuItem key={item.title}>
              <SidebarMenuButton asChild className="text-muted-foreground" size="sm">
                <Link to={item.path ?? '/'}>
                  {item.icon}
                  <span>{item.title}</span>
                </Link>
              </SidebarMenuButton>
            </SidebarMenuItem>
          ))}
        </SidebarMenu>
        <div className="px-4 pt-4 pb-2 transition-opacity group-data-[collapsible=icon]:pointer-events-none group-data-[collapsible=icon]:opacity-0">
          <p className="text-nowrap text-[9px] text-muted-foreground">© {new Date().getFullYear()} AnimeTracker</p>
        </div>
      </SidebarFooter>
    </Sidebar>
  );
}
