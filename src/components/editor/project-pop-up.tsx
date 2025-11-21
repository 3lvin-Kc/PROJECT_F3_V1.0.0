import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ProjectSettingsPopupProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  projectName: string;
  onProjectNameChange: (name: string) => void;
}

export const ProjectSettingsPopup = ({
  open,
  onOpenChange,
  projectName,
  onProjectNameChange,
}: ProjectSettingsPopupProps) => {
  const [tempProjectName, setTempProjectName] = useState(projectName);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    onProjectNameChange(tempProjectName);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent 
        className="max-w-[1150px] max-h-[540px] w-[1150px] h-[540px] p-0 overflow-hidden"
        style={{ width: '1150px', height: '540px' }}
      >
        <DialogHeader className="p-6 pb-4 border-b">
          <DialogTitle>Project Settings</DialogTitle>
          <DialogDescription>
            Configure your project settings and preferences
          </DialogDescription>
        </DialogHeader>
        
        <div className="p-6 overflow-y-auto max-h-[calc(540px-80px)]">
          <form onSubmit={handleSubmit} className="space-y-6">
            <div className="space-y-2">
              <Label htmlFor="projectName">Project Name</Label>
              <Input
                id="projectName"
                value={tempProjectName}
                onChange={(e) => setTempProjectName(e.target.value)}
                placeholder="Enter project name"
              />
            </div>
            
            <div className="flex justify-end gap-3 pt-4">
              <Button
                type="button"
                variant="outline"
                onClick={() => onOpenChange(false)}
              >
                Cancel
              </Button>
              <Button type="submit">Save Changes</Button>
            </div>
          </form>
        </div>
      </DialogContent>
    </Dialog>
  );
};