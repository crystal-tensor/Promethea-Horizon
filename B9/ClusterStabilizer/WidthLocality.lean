import Mathlib.Data.Real.Basic

namespace B9

structure SpectralSummary where
  gap : Real
  width : Real
  normalizedGap : Real
  locality : Nat

section ClusterStabilizer
namespace ClusterStabilizer

def RawGapAmplifies (before after : SpectralSummary) : Prop :=
  after.gap > before.gap

def NormalizedGapInvariant (before after : SpectralSummary) : Prop :=
  after.normalizedGap = before.normalizedGap

def LocalityPreserved (before after : SpectralSummary) : Prop :=
  after.locality = before.locality

theorem uniform_scale_raw_gap_is_not_certificate
    (before after : SpectralSummary)
    (hRaw : RawGapAmplifies before after)
    (hInvariant : NormalizedGapInvariant before after) :
    not (after.normalizedGap > before.normalizedGap) := by
  intro hImp
  rw [hInvariant] at hImp
  exact lt_irrefl before.normalizedGap hImp

theorem cluster_stabilizer_open_uniform_reweight_obligation
    (n : Nat)
    (hN : 4 <= n)
    (before after : SpectralSummary)
    (hLocality : LocalityPreserved before after)
    (hRaw : RawGapAmplifies before after)
    (hInvariant : NormalizedGapInvariant before after) :
    after.locality = before.locality /\
      not (after.normalizedGap > before.normalizedGap) := by
  constructor
  . exact hLocality
  . exact uniform_scale_raw_gap_is_not_certificate before after hRaw hInvariant

end ClusterStabilizer

section SupportSize

def SupportSet : Set Nat := {2, 3}

def HasSupportSize (summary : SpectralSummary) : Prop :=
  summary.locality in SupportSet

theorem locality_in_support_set (summary : SpectralSummary) (hLoc : HasSupportSize summary) :
    summary.locality in SupportSet := hLoc

def MaxLocalityPreserved (before after : SpectralSummary) : Prop :=
  after.locality <= before.locality

theorem uniform_scale_preserves_max_locality
    (before after : SpectralSummary)
    (hLoc : LocalityPreserved before after) :
    MaxLocalityPreserved before after := by
  rw [hLoc]
  exact le_refl before.locality

end SupportSize

section UniformScaling

def UniformScaleFactor : Real := 27/20

def IsUniformlyScaled (before after : SpectralSummary) : Prop :=
  after.gap = UniformScaleFactor * before.gap /\
  after.width = UniformScaleFactor * before.width

theorem uniform_scale_preserves_normalized_gap
    (before after : SpectralSummary)
    (hScale : IsUniformlyScaled before after) :
    NormalizedGapInvariant before after := by
  rcases hScale with (hGap, hWidth)
  unfold NormalizedGapInvariant normalizedGap
  field_simp
  calc
    after.gap / after.width
        = (UniformScaleFactor * before.gap) / (UniformScaleFactor * before.width) := by
      simp [hGap, hWidth]
    _ = before.gap / before.width := by
      field_simp

end UniformScaling

section SpectralWidth

def SpectralWidthPreserved (before after : SpectralSummary) : Prop :=
  after.width / after.gap = before.width / before.gap

theorem uniform_scale_preserves_spectral_width_ratio
    (before after : SpectralSummary)
    (hScale : IsUniformlyScaled before after) :
    SpectralWidthPreserved before after := by
  rcases hScale with (hGap, hWidth)
  simp [SpectralWidthPreserved, hGap, hWidth]

end SpectralWidth

end B9
