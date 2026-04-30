import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { ProfileForm } from "./ProfileForm";

describe("ProfileForm", () => {
  it("submits the current display name", async () => {
    const onSave = vi.fn().mockResolvedValue(undefined);

    render(<ProfileForm profile={{ email: "a@example.com", displayName: "Adi" }} onSave={onSave} />);

    await userEvent.clear(screen.getByLabelText("Display name"));
    await userEvent.type(screen.getByLabelText("Display name"), "Adhi");
    await userEvent.click(screen.getByRole("button", { name: "Save" }));

    expect(onSave).toHaveBeenCalledWith({ displayName: "Adhi" });
  });
});
