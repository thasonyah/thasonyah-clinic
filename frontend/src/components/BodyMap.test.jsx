import { describe, it, expect } from "vitest";
import { readMarks } from "./BodyMap";
import { ageAt } from "../pages/staff/Records";

describe("clinical display helpers", () => {
  it("does not invent an age for missing DOB and respects the birthday", () => {
    expect(ageAt(null)).toBe(null);
    expect(ageAt("2000-09-13", new Date(2026, 8, 12))).toBe(25);
    expect(ageAt("2000-09-13", new Date(2026, 8, 13))).toBe(26);
  });
  it("rejects invalid coordinates and handles damaged saved content", () => {
    expect(readMarks("invalid")).toEqual([]);
    expect(readMarks('{"view":"หน้า"}')).toEqual([]);
    expect(
      readMarks(
        JSON.stringify([
          { view: "หน้า", x: 50, y: 10 },
          { view: "หลัง", x: -1, y: 20 },
          { view: "wrong", x: 1, y: 1 },
        ]),
      ),
    ).toEqual([{ view: "หน้า", x: 50, y: 10 }]);
  });
});
