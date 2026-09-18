"use client";

import { IconContext } from "@phosphor-icons/react";
import type { ReactNode } from "react";

export {
  QrCode, Scan, Camera, Barcode,
  Package, Truck, Warehouse, Stack, Cube,
  Wrench, MagnifyingGlass, ClipboardText, Gear, Factory,
  Check, CheckCircle, CheckSquare, XCircle, Warning, WarningCircle, Info, SealCheck,
  Play, Pause, StopCircle, ArrowsClockwise,
  Clock, Timer, CalendarBlank, ChartBar, ListNumbers, Table,
  ArrowLeft, ArrowRight, CaretDown, CaretLeft, CaretRight, CaretUp, List, SidebarSimple, X,
  User, UserSwitch, SignOut, SignIn, Lock, DeviceTablet,
  Plus, Minus, Trash, Printer, DownloadSimple, UploadSimple, Copy, ImageSquare,
  TextAa, Sun, Moon, Desktop,
} from "@phosphor-icons/react";

export function IconProvider({ children }: { children: ReactNode }) {
  return (
    <IconContext.Provider value={{ size: 24, weight: "regular" }}>
      {children}
    </IconContext.Provider>
  );
}
